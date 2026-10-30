"""H3 training closure + DISK-ONLY checkpoint-selection replay (supervisor section 8/9/10/11).

FAIL-CLOSED. This script refuses to produce any closure while the experiment
registry still reports the H3 run as RUNNING. It instantiates NO model, runs NO
forward pass, NO training, NO TEST access, and NO supply-axis evaluation. It
reads only persisted disk artifacts:

  experiments/<EXP_ID>/history.csv          (per-epoch trainer records)
  experiments/<EXP_ID>/training.log         (per-epoch best flags)
  experiments/registry.{json,csv}           (final run status / end time)
  checkpoints/<EXP_ID>/{best,latest}.pt     (metadata ONLY, map_location cpu)
  reports/audits/*binding*.json             (frozen launch / pretraining bindings)

Outputs (ADDITIVE; never overwrites the launch or pretraining bindings):
  reports/audits/h3_proposal_supply_training_closure.json
  reports/audits/h3_checkpoint_selection_replay.json

Required replay verdict for a PASS closure:
  H3_CHECKPOINT_SELECTION_REPLAY_PASS
"""
import ast
import datetime
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
from src.training.clean_v3_selection import (H3_SUPPLY_TERM_NAMES,
                                             select_h3_supply_epoch)

EXP_ID = 'h3_kub_localizer_sigma_adaptive_sizeaware_seed42_clean_v3'
EXP = ROOT / 'experiments' / EXP_ID
CHK = ROOT / 'checkpoints' / EXP_ID
AUDITS = ROOT / 'reports' / 'audits'
PATIENCE = 15
MAX_EPOCHS = 100
FROZEN_DECODE = {'threshold': 0.10, 'margin': 0.20, 'top_k': 5, 'nms_iou': 0.30}
A_REF = 13.0
SIGMA_MIN, SIGMA_MAX = 0.35, 0.75
TRAIN_POP = {'images': 770, 'canonical_components': 1161}
VAL_POP = {'images': 103, 'canonical_components': 152, 'tiny_components': 72}
ORPHAN = 'ef36ad8332b2f33882dc668a5b6846e5'
H3_TERM_NAMES = list(H3_SUPPLY_TERM_NAMES)

# Evidence-based trainer revision lineage (supervisor: multi-SHA implementation
# lineage). Segment 1 = process launched 2026-09-25T06:03:40Z from the launch
# binding (epochs 1-2). Segment 2 = process launched 2026-09-25T07:58:25Z from
# the 13:57-local revised trainer (epochs 3+). The launch-era trainer bytes are
# not recoverable locally (git HEAD predates H3; __pycache__ matches current).
TRAINER_LINEAGE = {
    'design_binding_v2': None,  # replaced at runtime with the full SHA from pretraining binding v2 implementation_sha256
    'launch_binding_segment_1_epochs_1_2': '9099d6de339aba43d5e92284ea741568f16c7f5c39e7c189c595301ca5cb88f9',
    'segment_2_epochs_3_plus_expected': '45bef74f4eddb2e376fd768b1da2e0cba743897e30a725241ac6882d60ad3578',
}
SEGMENT_BOUNDARY_EPOCH = 2  # epochs <= 2 produced by launch-era trainer
SEGMENT_2_PROCESS_START_UTC = '2026-09-25T07:58:25Z'
INTERRUPTION_AFTER_EPOCH = 2
INTERRUPTION_EVIDENCE = {
    'last_segment_1_artifact': 'experiments/' + EXP_ID + '/h3_train_stdout.log (mtime 2026-09-25T06:17:39Z)',
    'no_completion_markers': 'registry end_time absent while RUNNING; no stop marker in training.log at interruption time',
    'resume_source': 'checkpoints/' + EXP_ID + '/latest.pt (epoch-2 full state)',
    'full_state_restored': ['model_state', 'optimizer_state', 'scheduler_state', 'grad_scaler_state',
                            'epoch', 'global_step', 'best_validation_score', 'training_history',
                            'early_stopping_state (bad_epochs)', 'loader_generator_states (train RNG)'],
    'continuity_evidence': [
        'learning_rate epoch 3 = 9.9778098e-05 = exact CosineAnnealingLR(T_max=100) value at step 2 (schedule state restored, not restarted)',
        'history.csv appended (epochs 1-2 rows and val_search_epoch001/002.csv untouched by segment 2)',
        'single registry row (register_experiment deduplicates by experiment_id)',
        'launch binding preserved (reports/audits/h3_training_launch_binding.json not rewritten at resume)',
    ],
}

REQUIRED_HISTORY_COLUMNS = [
    'epoch', 'train_loss', 'val_loss', 'val_hard_tiny_recovered90',
    'val_global_empty_images_covered90', 'val_tiny_recall90', 'val_overall_recall90',
    'learning_rate', 'epoch_seconds', 'peak_gpu_allocated', 'peak_gpu_reserved',
    'feasible_config_count', 'localization_status', 'mean_roi_area_fraction',
    'mean_proposals_per_image', 'mean_max_heatmap', 'median_max_heatmap',
    'fixed_decode', 'val_localization_recall', 'per_size_recall90',
    'any_overlap_recall', 'coverage50_recall', 'mean_coverage',
    'zero_proposal_gt', 'zero_proposal_tiny', 'total_gt_components',
    'total_proposals', 'precision', 'background_fraction',
    'selection_tuple', 'selection_term_names',
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path):
    with open(path, 'r', encoding='utf-8') as handle:
        return json.load(handle)


def now_utc() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def literal(value):
    return ast.literal_eval(value) if isinstance(value, str) else value


def guard_registry_complete():
    """FAIL-CLOSED: the run must have NATURALLY TERMINATED before any closure."""
    registry_json = ROOT / 'experiments' / 'registry.json'
    registry_csv = ROOT / 'experiments' / 'registry.csv'
    if not registry_json.exists() or not registry_csv.exists():
        raise RuntimeError('REGISTRY_GUARD_FAILED: experiments/registry.{json,csv} not found')
    records = load_json(registry_json)
    matches = [r for r in records if r.get('experiment_id') == EXP_ID]
    if len(matches) != 1:
        raise RuntimeError(f'REGISTRY_GUARD_FAILED: expected exactly 1 registry record for {EXP_ID}, found {len(matches)}')
    rec = matches[0]
    status = rec.get('status')
    end_time = rec.get('end_time')
    if status == 'RUNNING' or not end_time:
        raise RuntimeError(
            'REGISTRY_GUARD_FAILED: H3 run is still RUNNING (or terminated without natural '
            f'completion). status={status!r} end_time={end_time!r}. '
            'Training closure may only be created after NATURAL termination.')
    if status not in ('TRAINED', 'NO_FEASIBLE_LOCALIZER'):
        raise RuntimeError(f'REGISTRY_GUARD_FAILED: unexpected terminal status {status!r}')
    csv_rows = pd.read_csv(registry_csv)
    n_csv = int((csv_rows['experiment_id'] == EXP_ID).sum())
    if n_csv != 1:
        raise RuntimeError(f'REGISTRY_GUARD_FAILED: registry.csv has {n_csv} rows for {EXP_ID}; duplicate-run governance conflict')
    return rec


def verify_history():
    """Section 8: full training-history integrity."""
    path = EXP / 'history.csv'
    hist = pd.read_csv(path)
    missing = [c for c in REQUIRED_HISTORY_COLUMNS if c not in hist.columns]
    if missing:
        raise RuntimeError(f'HISTORY_INTEGRITY_FAILED: missing columns {missing}')
    epochs = hist['epoch'].astype(int).tolist()
    n = len(epochs)
    if epochs != list(range(1, n + 1)):
        raise RuntimeError(f'HISTORY_INTEGRITY_FAILED: epochs not unique/ordered/contiguous 1..{n}: {epochs[:5]}...{epochs[-5:]}')
    for col in ('train_loss', 'val_loss', 'val_localization_recall', 'learning_rate', 'epoch_seconds'):
        bad = hist[col].isna() | ~pd.to_numeric(hist[col], errors='coerce').apply(lambda v: v == v and abs(v) != float('inf'))
        if bad.any():
            raise RuntimeError(f'HISTORY_INTEGRITY_FAILED: non-finite values in {col} at epochs {hist.loc[bad, "epoch"].tolist()}')
    decode_mismatch = [e for e, v in zip(epochs, hist['fixed_decode']) if literal(v) != FROZEN_DECODE]
    if decode_mismatch:
        raise RuntimeError(f'HISTORY_INTEGRITY_FAILED: fixed_decode drift at epochs {decode_mismatch}')
    terms_mismatch = [e for e, v in zip(epochs, hist['selection_term_names']) if list(literal(v)) != H3_TERM_NAMES]
    if terms_mismatch:
        raise RuntimeError(f'HISTORY_INTEGRITY_FAILED: selection_term_names drift at epochs {terms_mismatch}')
    tuple_mismatch = []
    for _, r in hist.iterrows():
        st = list(literal(r['selection_tuple']))
        if len(st) != 2 or abs(st[0] - float(r['val_localization_recall'])) > 1e-12 or abs(st[1] - (-float(r['val_loss']))) > 1e-12:
            tuple_mismatch.append(int(r['epoch']))
    if tuple_mismatch:
        raise RuntimeError(f'HISTORY_INTEGRITY_FAILED: selection_tuple != (val_localization_recall, -val_loss) at epochs {tuple_mismatch}')
    gt_mismatch = [int(e) for e, v in zip(epochs, hist['total_gt_components']) if int(v) != VAL_POP['canonical_components']]
    if gt_mismatch:
        raise RuntimeError(f'HISTORY_INTEGRITY_FAILED: total_gt_components != 152 at epochs {gt_mismatch}')
    cfg_mismatch = [int(e) for e, v in zip(epochs, hist['feasible_config_count']) if int(v) != 1]
    if cfg_mismatch:
        raise RuntimeError(f'HISTORY_INTEGRITY_FAILED: feasible_config_count != 1 (proposal configurations per epoch) at epochs {cfg_mismatch}')
    for col in ('zero_proposal_gt', 'zero_proposal_tiny', 'total_proposals', 'precision', 'background_fraction'):
        if hist[col].isna().any():
            raise RuntimeError(f'HISTORY_INTEGRITY_FAILED: NaN in {col}')
    return hist, n


def parse_training_log_flags(n_epochs):
    """Trainer-recorded is_new_best equivalent: the per-epoch 'best=' flag."""
    path = EXP / 'training.log'
    flags = {}
    for line in path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line.startswith('Epoch '):
            continue
        parts = line.split()
        try:
            epoch = int(parts[1])
        except (ValueError, IndexError):
            continue
        if 'best=True' in line:
            flags[epoch] = True
        elif 'best=False' in line:
            flags[epoch] = False
    if sorted(flags) != list(range(1, n_epochs + 1)):
        raise RuntimeError(f'TRAINING_LOG_INTEGRITY_FAILED: best-flag epochs {sorted(flags)[:5]}...{sorted(flags)[-5:]} != 1..{n_epochs}')
    return flags


def replay_selection(hist):
    """Section 10: DISK-ONLY replay of the frozen 2-term selection rule."""
    best_score = None
    best_epoch = None
    bad_epochs = 0
    stopped_epoch = None
    rows = []
    for _, r in hist.iterrows():
        epoch = int(r['epoch'])
        vlr = float(r['val_localization_recall'])
        vl = float(r['val_loss'])
        out = select_h3_supply_epoch(vlr, vl, best_score=best_score, best_epoch=best_epoch,
                                     bad_epochs=bad_epochs, epoch=epoch, patience=PATIENCE)
        rows.append({'epoch': epoch, 'val_localization_recall': vlr, 'val_loss': vl,
                     'selection_tuple': list(out.score),
                     'is_new_best': bool(out.is_new_best), 'bad_epochs': int(out.bad_epochs),
                     'best_epoch_so_far': int(out.best_epoch) if out.best_epoch is not None else None})
        best_score = out.best_score
        best_epoch = out.best_epoch
        bad_epochs = out.bad_epochs
        if out.stopped:
            stopped_epoch = epoch
            break
    return rows, best_epoch, tuple(best_score) if best_score else None, bad_epochs, stopped_epoch


def main():
    registry = guard_registry_complete()
    hist, n_epochs = verify_history()
    log_flags = parse_training_log_flags(n_epochs)
    replay_rows, best_epoch, best_score, final_bad_epochs, stopped_epoch = replay_selection(hist)

    flag_mismatches = [r['epoch'] for r in replay_rows if r['is_new_best'] != log_flags.get(r['epoch'])]
    if flag_mismatches:
        raise RuntimeError(f'REPLAY_HISTORY_MISMATCH: replayed new-best flags disagree with training.log at epochs {flag_mismatches}')

    # Stop reason (section 7). Replay and trainer share the same helper and
    # patience, so a replay stop at the final epoch means the trainer's own
    # early-stop condition fired there. If that coincides with epoch 100, max
    # epochs is the binding constraint but the condition was also met.
    max_reached = (n_epochs == MAX_EPOCHS)
    stop_at_final = (stopped_epoch == n_epochs)
    if max_reached and stop_at_final:
        stop_reason = 'MAX_EPOCHS_REACHED_WITH_EARLY_STOP_CONDITION_ALSO_MET'
        early_fired = True
    elif max_reached:
        stop_reason = 'MAX_EPOCHS_REACHED'
        early_fired = False
    elif stop_at_final:
        stop_reason = 'EARLY_STOPPING_PATIENCE_15_FIRED'
        early_fired = True
    else:
        raise RuntimeError(
            f'CLOSURE_GUARD_FAILED: run did not naturally terminate: {n_epochs} epochs recorded, '
            f'no max-epochs reach and no early-stop (replay stop epoch={stopped_epoch}).')

    # History argmax over the frozen tuple (independent of the helper replay)
    tuples = [list(literal(v)) for v in hist['selection_tuple']]
    argmax_epoch = int(hist['epoch'].iloc[max(range(len(tuples)), key=lambda i: tuples[i])])

    # ---- Checkpoint integrity (section 11) ---------------------------------
    import torch
    best_pt, latest_pt = CHK / 'best.pt', CHK / 'latest.pt'
    for p in (best_pt, latest_pt):
        if not p.exists():
            raise RuntimeError(f'CHECKPOINT_INTEGRITY_FAILED: {p} missing')
    b_st = torch.load(best_pt, map_location='cpu', weights_only=False)
    l_st = torch.load(latest_pt, map_location='cpu', weights_only=False)
    for name, st in (('best.pt', b_st), ('latest.pt', l_st)):
        if st.get('experiment_id') != EXP_ID:
            raise RuntimeError(f'CHECKPOINT_INTEGRITY_FAILED: {name} experiment_id={st.get("experiment_id")!r} != {EXP_ID!r}')
    best_pt_epoch = int(b_st['epoch'])
    best_pt_score = [float(x) for x in b_st['best_validation_score']]
    latest_epoch = int(l_st['epoch'])
    early_state = l_st.get('early_stopping_state') or {}
    latest_bad_epochs = int(early_state.get('bad_epochs', -1))
    latest_stopped = bool(early_state.get('stopped', False))
    hist_in_latest = l_st.get('training_history') or []
    latest_hist_epochs = [int(row['epoch']) for row in hist_in_latest]

    checks = {
        'latest_epoch_equals_final_epoch': latest_epoch == n_epochs,
        'latest_history_epochs_match': latest_hist_epochs == list(range(1, n_epochs + 1)),
        'latest_bad_epochs_match_replay': latest_bad_epochs == final_bad_epochs,
        'latest_stopped_flag_matches_replay_stop_condition': latest_stopped == stop_at_final,
        'best_pt_epoch_matches_replay': best_pt_epoch == best_epoch,
        'best_pt_epoch_matches_history_argmax': best_pt_epoch == argmax_epoch,
        'best_pt_score_matches_replay': (abs(best_pt_score[0] - best_score[0]) < 1e-9
                                         and abs(best_pt_score[1] - best_score[1]) < 1e-9),
        'seed42': int(b_st.get('seed', -1)) == 42,
    }
    for row, ref in zip(hist_in_latest, hist.itertuples()):
        if abs(float(row['val_loss']) - float(ref.val_loss)) > 1e-9 or \
           abs(float(row['val_localization_recall']) - float(ref.val_localization_recall)) > 1e-9:
            raise RuntimeError(f'CHECKPOINT_INTEGRITY_FAILED: latest.pt training_history disagrees with history.csv at epoch {ref.epoch}')
    failed_checks = [k for k, v in checks.items() if not v]
    if failed_checks:
        raise RuntimeError(f'CHECKPOINT_INTEGRITY_FAILED: {failed_checks}')

    best_sha, latest_sha = sha256_file(best_pt), sha256_file(latest_pt)
    history_sha = sha256_file(EXP / 'history.csv')
    trainer_sha = sha256_file(ROOT / 'scripts/training/train_phase13b_localizer.py')

    # ---- Scientific SHA verification against the frozen bindings -----------
    # The LAUNCH binding is the authoritative run-era reference (written after
    # the FAIL-CLOSED pre-launch checks, immediately before epoch 1). The
    # design-era pretraining binding v2 additionally freezes heatmap_targets,
    # which the launch binding does not record.
    launch = load_json(AUDITS / 'h3_training_launch_binding.json')
    prebind = load_json(AUDITS / 'h3_proposal_supply_final_pretraining_binding_v2.json')
    launch_shas = launch['final_shas']
    prebind_impl = prebind.get('implementation_sha256') or {}
    HEATMAP_KEY = 'src/inference/heatmap_targets.py'
    TRAINER_DESIGN_KEY = 'scripts/training/train_phase13b_localizer.py'
    DATASET_DESIGN_KEY = 'src/data/kub_localizer_dataset.py'
    for key in (HEATMAP_KEY, TRAINER_DESIGN_KEY, DATASET_DESIGN_KEY):
        if key not in prebind_impl:
            raise RuntimeError(f'SCIENTIFIC_CONFIG_DRIFT: pretraining binding v2 implementation_sha256 lacks {key}')
    module_paths = {
        'dataset_module': ROOT / 'src/data/kub_localizer_dataset.py',
        'selection_module': ROOT / 'src/training/clean_v3_selection.py',
        'checkpointing_module': ROOT / 'src/utils/checkpointing.py',
        'config': ROOT / 'configs/kub/phase13b_localizer_h3_size_adaptive_sigma.yaml',
        'train_manifest': ROOT / 'manifests/phase4_v3/train.csv',
        'val_manifest': ROOT / 'manifests/phase4_v3/val.csv',
    }
    sha_checks = {key: {'expected': launch_shas[key], 'actual': sha256_file(path)}
                  for key, path in module_paths.items()}
    heatmap_targets_sha = sha256_file(ROOT / HEATMAP_KEY)
    heatmap_drift = heatmap_targets_sha != prebind_impl[HEATMAP_KEY]
    sha_drift = [k for k, v in sha_checks.items() if v['actual'] != v['expected']]
    if sha_drift or heatmap_drift:
        raise RuntimeError(f'SCIENTIFIC_CONFIG_DRIFT: {sha_drift} heatmap_targets_drift={heatmap_drift}')

    trainer_lineage_full = dict(TRAINER_LINEAGE)
    trainer_lineage_full['design_binding_v2'] = prebind_impl[TRAINER_DESIGN_KEY]
    dataset_lineage = {
        'design_binding_v2': prebind_impl[DATASET_DESIGN_KEY],
        'launch_binding_run_era': launch_shas['dataset_module'],
        'note': ('dataset module was revised between the design-era pretraining binding and the '
                 'pre-launch safety check; the LAUNCH binding is the authoritative run-era '
                 'reference and current disk matches it byte-for-byte'),
    }

    replay_pass = all(checks.values()) and not flag_mismatches and best_epoch == argmax_epoch
    verdict = 'H3_CHECKPOINT_SELECTION_REPLAY_PASS' if replay_pass else 'H3_CHECKPOINT_SELECTION_REPLAY_MISMATCH'

    segment2_sha_matches = trainer_sha == TRAINER_LINEAGE['segment_2_epochs_3_plus_expected']
    producing_trainer = {e: TRAINER_LINEAGE['launch_binding_segment_1_epochs_1_2']
                         for e in range(1, SEGMENT_BOUNDARY_EPOCH + 1)}
    for e in range(SEGMENT_BOUNDARY_EPOCH + 1, n_epochs + 1):
        producing_trainer[e] = trainer_sha
    best_producing_trainer = producing_trainer.get(best_pt_epoch, trainer_sha)

    first_epoch_artifact = (EXP / 'val_search_epoch001.csv')
    last_epoch_artifact = (EXP / f'val_search_epoch{n_epochs:03d}.csv')
    stdout_segment1 = EXP / 'h3_train_stdout.log'

    timeline = [
        {'event': 'INITIAL_LAUNCH', 'time_utc': launch['timestamp_utc'],
         'epoch_range': f'1-{SEGMENT_BOUNDARY_EPOCH}', 'process_state': 'launched from launch binding',
         'trainer_sha': TRAINER_LINEAGE['launch_binding_segment_1_epochs_1_2'],
         'config_sha': sha_checks['config']['expected'],
         'resume_source': None, 'full_state_restored': None,
         'scientific_effect': 'frozen H3 contract enforced by FAIL-CLOSED pre-launch safety checks'},
        {'event': 'INTERRUPTION', 'time_utc': '2026-09-25T06:17:39Z (last segment-1 artifact write)',
         'epoch_range': f'after epoch {INTERRUPTION_AFTER_EPOCH}', 'process_state': 'process terminated without completion markers',
         'trainer_sha': TRAINER_LINEAGE['launch_binding_segment_1_epochs_1_2'],
         'config_sha': sha_checks['config']['expected'],
         'resume_source': None, 'full_state_restored': None,
         'scientific_effect': 'none (epoch-2 full state preserved in latest.pt)'},
        {'event': 'SAME_RUN_RESUME', 'time_utc': SEGMENT_2_PROCESS_START_UTC,
         'epoch_range': f'{SEGMENT_BOUNDARY_EPOCH + 1}-{n_epochs}', 'process_state': 'new process, same logical run',
         'trainer_sha': trainer_sha,
         'config_sha': sha_checks['config']['expected'],
         'resume_source': INTERRUPTION_EVIDENCE['resume_source'],
         'full_state_restored': INTERRUPTION_EVIDENCE['full_state_restored'],
         'scientific_effect': 'none (all scientific module SHAs byte-identical to launch binding; FAIL-CLOSED pre-launch checks re-passed; scheduler/history/selection state continued exactly)'},
        {'event': 'NATURAL_COMPLETION', 'time_utc': registry.get('end_time'),
         'epoch_range': f'final epoch {n_epochs}', 'process_state': f'registry status {registry.get("status")}',
         'trainer_sha': trainer_sha, 'config_sha': sha_checks['config']['expected'],
         'resume_source': None, 'full_state_restored': None,
         'scientific_effect': f'stop reason {stop_reason}'},
    ]

    replay_artifact = {
        'artifact': 'h3_checkpoint_selection_replay',
        'supervisor_ruling': 'H3_FINAL_LAUNCH_SAFETY_CHECK_PLUS_PROSPECTIVE_TRAINING_AUTHORIZATION__SECTION_10',
        'experiment_id': EXP_ID,
        'replay_method': 'DISK_ONLY__NO_MODEL_INSTANTIATION_NO_FORWARD_PASS_NO_TRAINING_NO_TEST',
        'selection_rule': 'MAX val_localization_recall then MIN val_loss (strict lexicographic tuple; exact ties are NOT improvements)',
        'selection_term_names': H3_TERM_NAMES,
        'frozen_decode': FROZEN_DECODE,
        'tie_handling': 'minimum val_loss only',
        'excluded_from_replay': ['tiny_recall gate', 'overall-recall feasibility rule', 'proposal area',
                                 'downstream Dice', 'FP burden', 'alternate proposal thresholds'],
        'epochs_replayed': n_epochs,
        'per_epoch_replay': [{**r, 'trainer_recorded_best_flag': log_flags.get(r['epoch']),
                              'flags_match': r['is_new_best'] == log_flags.get(r['epoch'])}
                             for r in replay_rows],
        'replay_selected_epoch': best_epoch,
        'replay_selected_score': list(best_score),
        'replay_selected_val_localization_recall': best_score[0],
        'replay_selected_val_loss': -best_score[1],
        'replay_stopped_epoch': stopped_epoch,
        'max_epochs_reached': max_reached,
        'early_stopping_fired': early_fired,
        'comparisons': {
            'history_tuple_argmax_epoch': argmax_epoch,
            'best_pt_epoch': best_pt_epoch,
            'best_pt_best_validation_score': best_pt_score,
            'best_pt_sha256': best_sha,
            'latest_pt_epoch': latest_epoch,
            'latest_pt_bad_epochs': latest_bad_epochs,
            'latest_pt_sha256': latest_sha,
            'training_log_best_flags_match_replay': not flag_mismatches,
            'selected_epoch_all_sources_match': replay_pass,
        },
        'verdict': verdict,
        'timestamp_utc': now_utc(),
    }

    closure = {
        'artifact': 'h3_proposal_supply_training_closure',
        'supervisor_ruling': 'H3_FINAL_LAUNCH_SAFETY_CHECK_PLUS_PROSPECTIVE_TRAINING_AUTHORIZATION__SECTIONS_7_8_9_11',
        'experiment_id': EXP_ID,
        'checkpoint_namespace': 'checkpoints/' + EXP_ID + '/',
        'final_training_status': registry.get('status'),
        'run_state_final': 'NATURALLY_COMPLETED',
        'run_classification': 'ONE_LOGICAL_RUN__TWO_PROCESS_SEGMENTS__SAME_RUN_RESUME__NO_DUPLICATES',
        'start_state': {
            'launch_binding_timestamp_utc': launch['timestamp_utc'],
            'segment_1_first_epoch_artifact_utc': datetime.datetime.fromtimestamp(
                first_epoch_artifact.stat().st_mtime, datetime.timezone.utc).isoformat() if first_epoch_artifact.exists() else None,
            'segment_2_process_start_utc': SEGMENT_2_PROCESS_START_UTC,
        },
        'end_state': {
            'registry_end_time_utc': registry.get('end_time'),
            'last_epoch_artifact_utc': datetime.datetime.fromtimestamp(
                last_epoch_artifact.stat().st_mtime, datetime.timezone.utc).isoformat() if last_epoch_artifact.exists() else None,
        },
        'total_epochs': n_epochs,
        'final_epoch': n_epochs,
        'stop_reason': stop_reason,
        'early_stopping_fired': early_fired,
        'max_epochs_reached': max_reached,
        'best_epoch': best_epoch,
        'best_val_localization_recall': best_score[0],
        'best_val_loss': -best_score[1],
        'best_selection_tuple': list(best_score),
        'final_bad_epochs': final_bad_epochs,
        'patience': PATIENCE,
        'seed': 42,
        'train_population': {**TRAIN_POP, 'orphan_excluded': True, 'orphan_sample_id': ORPHAN},
        'val_population': VAL_POP,
        'model': {
            'architecture': 'compact_unet_heatmap', 'factory': 'kub_localizer',
            'in_channels': 1, 'out_channels': 1, 'base_channels': 16,
            'resolution': 512, 'heatmap_resolution': 128,
            'initialization': 'random (no pretrained weights)',
        },
        'target_support': {
            'formula': 'sigma_i = clip(0.35 + 0.40 * sqrt(A128_i / A_ref), 0.35, 0.75)',
            'A_ref': A_REF, 'sigma_min': SIGMA_MIN, 'sigma_max': SIGMA_MAX,
            'size_adaptive_sigma': True,
            'A_ref_source': 'p75 of TRAIN-only FULL_FIELD code-exact 128-space component areas (reports/tables/h3_aref_code_exact.json)',
        },
        'loss': 'CenterNetFocalLoss(alpha=2.0, beta=4.0, dice_weight=0.0)',
        'optimizer': 'AdamW(lr=1e-4, weight_decay=1e-4)',
        'scheduler': 'CosineAnnealingLR(T_max=100)',
        'proposal_decode': FROZEN_DECODE,
        'proposal_configurations_per_epoch': 1,
        'grid_search_enabled': False,
        'selection_rule': 'MAX val_localization_recall then MIN val_loss',
        'selection_term_names': H3_TERM_NAMES,
        'interruptions': [{
            'index': 1, 'after_epoch': INTERRUPTION_AFTER_EPOCH,
            'time_utc': '2026-09-25T06:17:39Z', 'cause': 'host process termination (exact cause not captured in artifacts)',
            'evidence': INTERRUPTION_EVIDENCE,
        }],
        'resumes': [{
            'index': 1, 'resumed_from_epoch': INTERRUPTION_AFTER_EPOCH,
            'time_utc': SEGMENT_2_PROCESS_START_UTC, 'resume_source': 'checkpoints/' + EXP_ID + '/latest.pt',
            'full_state_restored': INTERRUPTION_EVIDENCE['full_state_restored'],
            'continuity_evidence': INTERRUPTION_EVIDENCE['continuity_evidence'],
            'scientific_effect': 'none',
        }],
        'duplicate_runs': 0,
        'interruption_resume_timeline': timeline,
        'exact_invoked_command_segment_2': ('D:/Softfors/jup/.venv/Scripts/python.exe scripts/training/train_phase13b_localizer.py '
                                            '--h3 --config configs/kub/phase13b_localizer_h3_size_adaptive_sigma.yaml --sigma 0.75 '
                                            '--size_adaptive_sigma --selection_rule max_localization_recall'),
        'command_note': ('--h3 mode forces size_adaptive_sigma=True and selection_rule=max_localization_recall; '
                         'the explicit flags are redundant with --h3 and do not alter the frozen scientific configuration.'),
        'implementation_shas': {
            'trainer_current': trainer_sha,
            'trainer_lineage': trainer_lineage_full,
            'trainer_current_matches_segment_2_lineage': segment2_sha_matches,
            'trainer_per_epoch_producer': {str(k): v for k, v in producing_trainer.items()},
            'launch_binding_trainer_sha_epochs_1_2': TRAINER_LINEAGE['launch_binding_segment_1_epochs_1_2'],
            'launch_era_trainer_bytes_recoverable_locally': False,
            'dataset_module': sha_checks['dataset_module']['actual'],
            'dataset_module_lineage': dataset_lineage,
            'heatmap_targets_module': heatmap_targets_sha,
            'selection_helper_module': sha_checks['selection_module']['actual'],
            'checkpointing_module': sha_checks['checkpointing_module']['actual'],
            'config': sha_checks['config']['actual'],
            'train_manifest': sha_checks['train_manifest']['actual'],
            'val_manifest': sha_checks['val_manifest']['actual'],
            'history_csv': history_sha,
            'training_log': sha256_file(EXP / 'training.log'),
            'stdout_log_segment_1': sha256_file(stdout_segment1) if stdout_segment1.exists() else None,
            'stdout_log_segment_2': None,
            'stdout_log_segment_2_note': 'segment-2 console output was not captured to a file; per-epoch authoritative records are history.csv + training.log',
            'launch_binding': sha256_file(AUDITS / 'h3_training_launch_binding.json'),
            'pretraining_binding_v2': sha256_file(AUDITS / 'h3_proposal_supply_final_pretraining_binding_v2.json'),
            'best_pt': best_sha,
            'latest_pt': latest_sha,
        },
        'scientific_module_shas_match_launch_binding': True,
        'history_integrity': {
            'status': 'PASS', 'rows': n_epochs, 'epochs_contiguous_1_to_n': True,
            'columns': list(hist.columns), 'finite_metrics_verified': True,
            'total_gt_components_all_epochs': VAL_POP['canonical_components'],
            'fixed_decode_constant': True, 'selection_tuple_consistent': True,
            'feasible_config_count_all_epochs': 1,
        },
        'checkpoint_integrity': {
            'best_pt': {
                'path': str(best_pt), 'epoch': best_pt_epoch, 'sha256': best_sha,
                'selected_metric_values': {'val_localization_recall': best_pt_score[0], 'negative_val_loss': best_pt_score[1]},
                'producing_implementation': {'trainer_sha': best_producing_trainer,
                                              'checkpointing_module_sha': sha_checks['checkpointing_module']['actual']},
                'experiment_id': EXP_ID,
            },
            'latest_pt': {
                'path': str(latest_pt), 'epoch': latest_epoch, 'sha256': latest_sha,
                'bad_epochs': latest_bad_epochs, 'stopped': latest_stopped,
                'producing_implementation': {'trainer_sha': trainer_sha,
                                              'checkpointing_module_sha': sha_checks['checkpointing_module']['actual']},
                'experiment_id': EXP_ID,
            },
            'all_checks': checks,
        },
        'checkpoint_selection_replay': {
            'artifact': 'reports/audits/h3_checkpoint_selection_replay.json',
            'verdict': verdict,
            'selected_epoch': best_epoch,
        },
        'test_reads': 0,
        'external_test_reads': 0,
        'test_status': 'CLOSED',
        'phase_15_status': 'NOT_STARTED_AND_NOT_AUTHORIZED',
        'supply_axis_evaluation_status': 'PENDING__REQUIRES_SEPARATE_AUTHORIZATION_AFTER_CLOSURE_AND_REPLAY_PASS',
        'downstream_refiner_evaluation_status': 'NOT_PERFORMED_IN_THIS_TASK',
        'status': ('H3_TRAINING_COMPLETE__CHECKPOINT_SELECTION_REPLAY_PASS__SUPPLY_EVALUATION_PENDING'
                   if replay_pass else
                   'H3_TRAINING_COMPLETE__CHECKPOINT_SELECTION_REPLAY_MISMATCH__STOPPED_BEFORE_SUPPLY_EVALUATION'),
        'timestamp_utc': now_utc(),
    }

    (AUDITS / 'h3_checkpoint_selection_replay.json').write_text(json.dumps(replay_artifact, indent=2), encoding='utf-8')
    (AUDITS / 'h3_proposal_supply_training_closure.json').write_text(json.dumps(closure, indent=2), encoding='utf-8')

    print(json.dumps({
        'epochs': n_epochs, 'stop_reason': stop_reason, 'best_epoch': best_epoch,
        'best_val_localization_recall': best_score[0], 'best_val_loss': -best_score[1],
        'replay_verdict': verdict, 'closure_status': closure['status'],
        'best_pt_sha256': best_sha, 'latest_pt_sha256': latest_sha,
    }, indent=2))
    return replay_pass


if __name__ == '__main__':
    ok = main()
    sys.exit(0 if ok else 1)
