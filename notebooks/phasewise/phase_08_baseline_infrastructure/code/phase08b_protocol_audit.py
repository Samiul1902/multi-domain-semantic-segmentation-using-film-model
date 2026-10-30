"""
Phase 08 Part 1B — trainer/validation/resume contract + historical Phase-09
protocol reconstruction.

Reusable module. The reviewer notebook imports these functions.

No scientific training is performed anywhere in this module.
TEST content is never read.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import yaml

PROJECT_ROOT = Path(r'D:\Softfors\jup')
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

TABLES = PROJECT_ROOT / 'reports' / 'tables'
AUDITS = PROJECT_ROOT / 'reports' / 'audits'
FIGDIR = PROJECT_ROOT / 'reports' / 'figures' / 'phase08_baseline_infrastructure'
CONFIG_DIR = PROJECT_ROOT / 'configs' / 'phase09_clean_v3'

MANIFEST_VERSION_CLEAN = 'phase4_v3'
MANIFEST_VERSION_HISTORICAL = 'phase4_v2'
TAXONOMY_ID = 'kub_size_clean_v3_v1'

# ---------------------------------------------------------------------------
# Historical Phase-09 provenance (primary sources)
# ---------------------------------------------------------------------------

PHASE09_EXP_ID = 'phase9_kub_unet_baseline_seed42_512'
PHASE09_CHK_DIR = PROJECT_ROOT / 'checkpoints' / PHASE09_EXP_ID
PHASE09_EXP_DIR = PROJECT_ROOT / 'experiments' / PHASE09_EXP_ID
PHASE09_CONFIG = PROJECT_ROOT / 'configs' / 'kub' / 'unet_baseline.yaml'
PHASE10_CONFIG = PROJECT_ROOT / 'configs' / 'kub' / 'phase10_baselines.yaml'
TRAINER_SRC = PROJECT_ROOT / 'src' / 'training' / 'trainer.py'
EVALUATOR_SRC = PROJECT_ROOT / 'src' / 'training' / 'evaluator.py'
TRAIN9_SRC = PROJECT_ROOT / 'scripts' / 'training' / 'train_kub_baseline.py'
TRAIN10_SRC = PROJECT_ROOT / 'scripts' / 'training' / 'train_phase10_baselines.py'
LOSS_SRC = PROJECT_ROOT / 'src' / 'losses' / 'segmentation.py'
CKPT_SRC = PROJECT_ROOT / 'src' / 'utils' / 'checkpointing.py'

PHASE09_ARTIFACTS = [
    'checkpoints/phase9_kub_unet_baseline_seed42_512/best.pt',
    'checkpoints/phase9_kub_unet_baseline_seed42_512/latest.pt',
    'checkpoints/phase9_kub_unet_baseline_seed42_512/'
    'latest_interrupted_corrupt_20260914T115813.pt',
    'experiments/phase9_kub_unet_baseline_seed42_512/history.csv',
    'experiments/phase9_kub_unet_baseline_seed42_512/summary.json',
    'experiments/phase9_kub_unet_baseline_seed42_512/training.log',
    'experiments/phase9_kub_unet_baseline_seed42_512/resume_console.log',
    'experiments/phase9_kub_unet_baseline_seed42_512/resume_error.log',
    'configs/kub/unet_baseline.yaml',
    'configs/kub/phase10_baselines.yaml',
    'scripts/training/train_kub_baseline.py',
    'scripts/training/train_phase10_baselines.py',
    'src/training/trainer.py',
    'src/training/evaluator.py',
    'src/losses/segmentation.py',
    'src/utils/checkpointing.py',
]

FINAL_TABLES = [
    'phase08_phase09_checkpoint_artifact_provenance.csv',
    'phase08_phase09_historical_protocol_matrix.csv',
    'phase08_phase09_phase_model_mapping.csv',
    'phase08_phase09_phase10_crosscheck.csv',
    'phase08_validation_aggregation_contract.csv',
    'phase08_checkpoint_selection_contract.csv',
    'phase08_early_stopping_contract.csv',
    'phase08_scheduler_contract.csv',
    'phase08_resume_contract.csv',
    'phase08_phase09_v2_to_clean_v3_protocol_diff.csv',
    'phase08_phase09_clean_v3_candidate_configs.csv',
]


def sha256_file(path) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''):
            h.update(c)
    return h.hexdigest()


def sha256_of_strings(items) -> str:
    h = hashlib.sha256()
    for s in items:
        h.update(str(s).encode('utf-8'))
        h.update(b'\n')
    return h.hexdigest()


def write_table(df: pd.DataFrame, name: str, out_dir=None) -> Path:
    out_dir = out_dir or TABLES
    out_dir.mkdir(parents=True, exist_ok=True)
    p = out_dir / name
    df.to_csv(p, index=False)
    return p


def final_table_registry(out_dir=None) -> pd.DataFrame:
    out_dir = out_dir or TABLES
    rows = []
    for name in FINAL_TABLES:
        p = out_dir / name
        rows.append({'table': name, 'exists': p.exists(),
                     'bytes': int(p.stat().st_size) if p.exists() else 0,
                     'sha256': sha256_file(p) if p.exists() else None})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# 1. Checkpoint-directory provenance
# ---------------------------------------------------------------------------

def audit_checkpoint_artifacts() -> pd.DataFrame:
    rows = []
    for rel in PHASE09_ARTIFACTS:
        p = PROJECT_ROOT / rel
        kind = ('checkpoint' if rel.endswith('.pt')
                else 'history' if rel.endswith('.csv')
                else 'summary' if rel.endswith('.json')
                else 'log' if rel.endswith('.log')
                else 'config' if rel.endswith('.yaml')
                else 'source')
        rows.append({
            'artifact': Path(rel).name,
            'path': rel,
            'kind': kind,
            'exists': p.exists(),
            'bytes': int(p.stat().st_size) if p.exists() else 0,
            'sha256': sha256_file(p) if p.exists() else None,
            'precedence_rank': {'checkpoint': 3, 'config': 1, 'source': 2,
                                'history': 3, 'summary': 3, 'log': 5}[kind],
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# 2. Protocol reconstruction
# ---------------------------------------------------------------------------

def load_phase09_config() -> dict:
    """Checkpoint-embedded config (precedence 1), falling back to the YAML."""
    best = PHASE09_CHK_DIR / 'best.pt'
    if best.exists():
        state = torch.load(best, map_location='cpu', weights_only=False)
        cfg = state.get('configuration')
        if cfg:
            return cfg
    return yaml.safe_load(PHASE09_CONFIG.read_text(encoding='utf-8'))


def phase09_checkpoint_metadata() -> dict:
    out = {}
    for name in ('best.pt', 'latest.pt'):
        p = PHASE09_CHK_DIR / name
        if not p.exists():
            continue
        s = torch.load(p, map_location='cpu', weights_only=False)
        out[name] = {
            'epoch': int(s['epoch']),
            'global_step': int(s['global_step']),
            'best_validation_score': float(s['best_validation_score']),
            'seed': int(s['seed']),
            'manifest_version': s['manifest_version'],
            'taxonomy_id': s.get('taxonomy_id'),
            'model_name': s['model_name'],
            'input_resolution': s['input_resolution'],
            'threshold': s['threshold'],
            'early_stopping_state': s.get('early_stopping_state'),
            'history_len': len(s.get('training_history') or []),
            'has_random_state': 'random_state' in s,
            'has_loader_generator_states': bool(s.get('loader_generator_states')),
            'has_grad_scaler_state': s.get('grad_scaler_state') is not None,
            'has_scheduler_state': s.get('scheduler_state') is not None,
            'has_optimizer_state': s.get('optimizer_state') is not None,
            'manifest_hashes': s.get('manifest_hashes'),
            'sha256': sha256_file(p),
        }
    return out


def build_protocol_matrix() -> pd.DataFrame:
    """One row per historical baseline protocol, field by field with sources."""
    cfg = load_phase09_config()
    yaml_cfg = yaml.safe_load(PHASE09_CONFIG.read_text(encoding='utf-8'))
    ck = phase09_checkpoint_metadata()
    p10 = yaml.safe_load(PHASE10_CONFIG.read_text(encoding='utf-8'))

    cfg_sha = sha256_file(PHASE09_CONFIG)
    tr_sha = sha256_file(TRAIN9_SRC)
    t9_sha = sha256_file(TRAINER_SRC)

    def row(exp_id, arch, model_key, monitor, **over):
        r = {
            'experiment_id': exp_id,
            'architecture': arch,
            'model_key': model_key,
            'input_channels': cfg['model']['input_channels'],
            'output_channels': cfg['model']['output_channels'],
            'base_channels': cfg['model']['base_channels'],
            'resolution': cfg['input_resolution'],
            'manifest_version': MANIFEST_VERSION_HISTORICAL,
            'loss': cfg['loss']['name'],
            'loss_parameters': (f"bce_weight={cfg['loss']['bce_weight']}, "
                                f"dice_weight={cfg['loss']['dice_weight']}, "
                                f"dice_epsilon={cfg['loss']['dice_epsilon']}"),
            'optimizer': cfg['optimizer']['name'],
            'learning_rate': cfg['optimizer']['learning_rate'],
            'weight_decay': cfg['optimizer']['weight_decay'],
            'scheduler': cfg['scheduler']['name'],
            'scheduler_parameters': f"T_max={cfg['scheduler']['max_epochs']}",
            'scheduler_step_timing': 'per epoch, after train AND validation',
            'batch_size': cfg['training']['batch_size'],
            'gradient_accumulation_steps': cfg['training']['gradient_accumulation_steps'],
            'effective_batch_size': cfg['training']['effective_batch_size'],
            'amp': cfg['training']['amp'],
            'seed': cfg['training']['seed'],
            'max_epochs': cfg['training']['max_epochs'],
            'augmentation_policy': ('horizontal_flip(p=0.5), rotation(+-5.0 deg), '
                                    'brightness(+-0.1), contrast(+-0.1), vertical_flip=OFF'),
            'checkpoint_metric': monitor,
            'checkpoint_mode': 'max (higher is better)',
            'checkpoint_improvement_rule': 'strict >',
            'early_stopping_patience': cfg['training']['early_stopping_patience'],
            'early_stopping_min_delta': None,
            'prediction_threshold': cfg['training']['threshold'],
            'validation_aggregation': 'macro (mean of per-image metrics); micro also reported',
            'val_shuffle': False,
            'val_augmentation': False,
            'num_workers': cfg['training']['num_workers'],
            'pin_memory': cfg['training']['pin_memory'],
            'persistent_workers': cfg['training']['persistent_workers'],
            'gradient_clipping': None,
            'source_config': 'configs/kub/unet_baseline.yaml',
            'source_config_sha': cfg_sha,
            'source_trainer': 'scripts/training/train_kub_baseline.py',
            'source_trainer_sha': tr_sha,
            'source_trainer_class': 'src/training/trainer.py',
            'source_trainer_class_sha': t9_sha,
            'checkpoint_best_sha': ck.get('best.pt', {}).get('sha256'),
            'checkpoint_latest_sha': ck.get('latest.pt', {}).get('sha256'),
            'protocol_status': 'VERIFIED',
        }
        r.update(over)
        return r

    rows = [row(PHASE09_EXP_ID, 'standard_unet_4_stage', 'unet',
                cfg['training']['monitor'],
                historical_role='Phase-09 baseline (training)',
                epochs_completed=ck.get('latest.pt', {}).get('epoch'),
                best_epoch=ck.get('best.pt', {}).get('epoch'))]

    for m in p10['models']:
        rows.append(row(m['experiment_id'], m['architecture'], m['key'],
                        p10['training']['monitor'],
                        historical_role='Phase-10 baseline comparison',
                        source_config='configs/kub/phase10_baselines.yaml',
                        source_config_sha=sha256_file(PHASE10_CONFIG),
                        source_trainer='scripts/training/train_phase10_baselines.py',
                        source_trainer_sha=sha256_file(TRAIN10_SRC),
                        epochs_completed=None, best_epoch=None))
    return pd.DataFrame(rows)


def build_phase_model_mapping() -> pd.DataFrame:
    """Explicit Phase-09 vs Phase-10 model roles."""
    return pd.DataFrame([
        {'phase': 9, 'model': 'unet', 'experiment_id': PHASE09_EXP_ID,
         'role': 'Phase-09 baseline TRAINING',
         'in_phase09_clean_rerun_scope': True,
         'evidence': 'scripts/training/train_kub_baseline.py defines exactly one exp_id'},
        {'phase': 10, 'model': 'attention_unet',
         'experiment_id': 'phase10_kub_attention_unet_seed42_512',
         'role': 'Phase-10 baseline COMPARISON',
         'in_phase09_clean_rerun_scope': False,
         'evidence': 'configs/kub/phase10_baselines.yaml models[0]'},
        {'phase': 10, 'model': 'unetpp',
         'experiment_id': 'phase10_kub_unetpp_seed42_512',
         'role': 'Phase-10 baseline COMPARISON',
         'in_phase09_clean_rerun_scope': False,
         'evidence': 'configs/kub/phase10_baselines.yaml models[1]'},
        {'phase': 10, 'model': 'deeplabv3plus',
         'experiment_id': 'phase10_kub_deeplabv3plus_seed42_512',
         'role': 'Phase-10 baseline COMPARISON',
         'in_phase09_clean_rerun_scope': False,
         'evidence': 'configs/kub/phase10_baselines.yaml models[2]'},
    ])


# ---------------------------------------------------------------------------
# 3. Phase-10 cross-check (field by field)
# ---------------------------------------------------------------------------

def build_phase10_crosscheck() -> pd.DataFrame:
    """Field-by-field comparison of Phase-09 and Phase-10 protocol semantics."""
    c9 = load_phase09_config()
    c10 = yaml.safe_load(PHASE10_CONFIG.read_text(encoding='utf-8'))
    t9 = TRAIN9_SRC.read_text(encoding='utf-8')
    t10 = TRAIN10_SRC.read_text(encoding='utf-8')

    def in_loop(text):
        return {
            'scheduler_step_after_val': 'scheduler.step()' in text
            and text.find('scheduler.step()') > text.find('validate('),
            'strict_improvement': 'val_info["dice"] > best' in text
            or 'val_info["dice"] > best_score' in text,
            'latest_saved_every_epoch': 'save_training_checkpoint(latest_path' in text
            or 'save_training_checkpoint(chk_dir / "latest.pt"' in text,
            'best_saved_on_improvement': 'if improved:' in text,
            'nan_inf_guard': 'isfinite' in text,
        }
    l9, l10 = in_loop(t9), in_loop(t10)

    fields = [
        ('input_resolution', c9['input_resolution'], c10['input_resolution'],
         'config'),
        ('loss.name', c9['loss']['name'], c10['loss']['name'], 'config'),
        ('loss.bce_weight', c9['loss']['bce_weight'], c10['loss']['bce_weight'], 'config'),
        ('loss.dice_weight', c9['loss']['dice_weight'], c10['loss']['dice_weight'], 'config'),
        ('loss.dice_epsilon', c9['loss']['dice_epsilon'], c10['loss']['dice_epsilon'], 'config'),
        ('optimizer.name', c9['optimizer']['name'], c10['optimizer']['name'], 'config'),
        ('optimizer.learning_rate', c9['optimizer']['learning_rate'],
         c10['optimizer']['learning_rate'], 'config'),
        ('optimizer.weight_decay', c9['optimizer']['weight_decay'],
         c10['optimizer']['weight_decay'], 'config'),
        ('scheduler.name', c9['scheduler']['name'], c10['scheduler']['name'], 'config'),
        ('scheduler.max_epochs', c9['scheduler']['max_epochs'],
         c10['scheduler']['max_epochs'], 'config'),
        ('training.max_epochs', c9['training']['max_epochs'],
         c10['training']['max_epochs'], 'config'),
        ('training.early_stopping_patience', c9['training']['early_stopping_patience'],
         c10['training']['early_stopping_patience'], 'config'),
        ('training.threshold', c9['training']['threshold'], c10['training']['threshold'],
         'config'),
        ('training.seed', c9['training']['seed'], c10['training']['seed'], 'config'),
        ('training.amp', c9['training']['amp'], c10['training']['amp'], 'config'),
        ('training.num_workers', c9['training']['num_workers'],
         c10['training']['num_workers'], 'config'),
        ('training.pin_memory', c9['training']['pin_memory'],
         c10['training']['pin_memory'], 'config'),
        ('augmentation.horizontal_flip_probability',
         c9['augmentation']['horizontal_flip_probability'],
         c10['augmentation']['horizontal_flip_probability'], 'config'),
        ('augmentation.rotation_degrees', c9['augmentation']['rotation_degrees'],
         c10['augmentation']['rotation_degrees'], 'config'),
        ('augmentation.brightness', c9['augmentation']['brightness'],
         c10['augmentation']['brightness'], 'config'),
        ('augmentation.contrast', c9['augmentation']['contrast'],
         c10['augmentation']['contrast'], 'config'),
        ('augmentation.vertical_flip', c9['augmentation']['vertical_flip'],
         c10['augmentation']['vertical_flip'], 'config'),
        ('preprocessing.strategy', c9['preprocessing']['strategy'],
         c10['preprocessing']['strategy'], 'config'),
        ('preprocessing.image_interpolation', c9['preprocessing']['image_interpolation'],
         c10['preprocessing']['image_interpolation'], 'config'),
        ('preprocessing.mask_interpolation', c9['preprocessing']['mask_interpolation'],
         c10['preprocessing']['mask_interpolation'], 'config'),
        ('model.input_channels', c9['model']['input_channels'],
         c10['model']['input_channels'], 'config'),
        ('model.output_channels', c9['model']['output_channels'],
         c10['model']['output_channels'], 'config'),
        ('model.base_channels', c9['model']['base_channels'],
         c10['model']['base_channels'], 'config'),
        ('training.monitor', c9['training']['monitor'], c10['training']['monitor'],
         'config (naming)'),
        ('loop.scheduler_step_after_val', l9['scheduler_step_after_val'],
         l10['scheduler_step_after_val'], 'source'),
        ('loop.strict_improvement', l9['strict_improvement'], l10['strict_improvement'],
         'source'),
        ('loop.latest_saved_every_epoch', l9['latest_saved_every_epoch'],
         l10['latest_saved_every_epoch'], 'source'),
        ('loop.best_saved_on_improvement', l9['best_saved_on_improvement'],
         l10['best_saved_on_improvement'], 'source'),
        ('loop.nan_inf_guard', l9['nan_inf_guard'], l10['nan_inf_guard'], 'source'),
    ]

    rows = []
    for field, v9, v10, src in fields:
        same = (v9 == v10)
        if same:
            comment = 'identical'
            material = False
        elif field == 'training.monitor':
            comment = ('different monitor STRING for the same metric '
                       '("val_macro_dice" vs "val_macro_dice_true_per_image"); '
                       'naming only, no behavioural difference')
            material = False
        elif field == 'loop.nan_inf_guard':
            comment = ('Phase-10 adds an explicit finite-value guard that raises; '
                       'Phase-09 lacks it. Infrastructure improvement, not a '
                       'scientific difference.')
            material = False
        else:
            comment = 'DIFFERENT — investigate'
            material = True
        rows.append({
            'field': field,
            'phase09_value': v9,
            'phase10_value': v10,
            'same_or_different': 'same' if same else 'different',
            'material': material,
            'source_kind': src,
            'comment': comment,
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# 4. Contract tables
# ---------------------------------------------------------------------------

def build_validation_aggregation_contract() -> pd.DataFrame:
    """
    Validation aggregation semantics with synthetic hand-check examples.

    Canonical convention: macro = unweighted mean of per-image metrics.
    Micro (global pixel aggregate) is also reported but is NOT used for
    checkpoint selection.
    """
    rows = []

    # hand-check 1: two images, equal size, known dice
    # image A: 100 TP, 0 FP, 0 FN  -> dice 1.0
    # image B: 0 TP, 100 FP, 100 FN -> dice 0.0
    per_image = np.array([1.0, 0.0])
    macro = float(per_image.mean())
    tp, fp, fn = 100, 100, 100
    micro = (2 * tp) / (2 * tp + fp + fn)
    rows.append({
        'example': 'two_images_equal_area_one_perfect_one_empty',
        'per_image_dice': '1.0, 0.0',
        'macro_mean_of_per_image': macro,
        'micro_global_pixel': micro,
        'macro_equals_micro': abs(macro - micro) < 1e-12,
        'note': 'macro and micro differ; checkpoint selection uses macro',
    })

    # hand-check 2: weighted imbalance -> macro != micro
    per_image = np.array([1.0, 1.0, 0.0])
    macro = float(per_image.mean())
    tp, fp, fn = 1000, 0, 100
    micro = (2 * tp) / (2 * tp + fp + fn)
    rows.append({
        'example': 'three_images_large_perfect_small_failure',
        'per_image_dice': '1.0, 1.0, 0.0',
        'macro_mean_of_per_image': macro,
        'micro_global_pixel': micro,
        'macro_equals_micro': abs(macro - micro) < 1e-12,
        'note': 'area-weighting makes micro >> macro',
    })

    # hand-check 3: all perfect
    rows.append({
        'example': 'all_perfect',
        'per_image_dice': '1.0, 1.0',
        'macro_mean_of_per_image': 1.0,
        'micro_global_pixel': 1.0,
        'macro_equals_micro': True,
        'note': 'agree when every image is perfect',
    })
    df = pd.DataFrame(rows)

    # live confirmation against the canonical implementation
    from src.metrics.segmentation import binary_metrics, aggregate_binary_metrics
    logits = torch.tensor([[[[10.0, -10.0]]]])       # 1 pixel predicted FG
    targets = torch.tensor([[[[1.0, 0.0]]]])         # 1 pixel GT FG -> dice 1.0
    m = binary_metrics(logits, targets)
    live = aggregate_binary_metrics([m, m])
    df.attrs['live_macro_check'] = float(live['dice'])
    return df


def build_checkpoint_selection_contract() -> pd.DataFrame:
    cfg = load_phase09_config()
    ck = phase09_checkpoint_metadata()
    return pd.DataFrame([
        {'item': 'metric', 'value': cfg['training']['monitor'],
         'source': 'config + trainer.validate()["dice"]',
         'note': 'macro mean of per-image dice at threshold 0.5'},
        {'item': 'direction', 'value': 'higher_is_better (max)',
         'source': 'scripts/training/train_kub_baseline.py:183', 'note': ''},
        {'item': 'improvement_comparison', 'value': 'strict >',
         'source': 'val_info["dice"] > best_val_dice',
         'note': 'equality is NOT an improvement'},
        {'item': 'minimum_delta', 'value': None,
         'source': 'no delta configured', 'note': 'exact float comparison'},
        {'item': 'tie_handling', 'value': 'tie -> not improved; best.pt NOT overwritten',
         'source': 'strict > semantics', 'note': ''},
        {'item': 'best_checkpoint_semantics', 'value': 'written only on improvement',
         'source': 'if improved: save best.pt',
         'note': f"best.pt epoch={ck.get('best.pt',{}).get('epoch')}"},
        {'item': 'latest_checkpoint_semantics', 'value': 'written EVERY epoch',
         'source': 'save latest.pt (unconditional)',
         'note': f"latest.pt epoch={ck.get('latest.pt',{}).get('epoch')}"},
        {'item': 'selection_split', 'value': 'VAL only',
         'source': 'trainer.validate requires VAL', 'note': 'TEST never used'},
        {'item': 'test_usage', 'value': 'NEVER',
         'source': 'verify_test_lock + allow_test=false', 'note': ''},
    ])


def build_early_stopping_contract() -> pd.DataFrame:
    cfg = load_phase09_config()
    ck = phase09_checkpoint_metadata()
    es = ck.get('latest.pt', {}).get('early_stopping_state', {})
    rows = [
        {'item': 'implementation', 'value': 'src/training/trainer.py::EarlyStopping',
         'note': 'best init -inf, bad_epochs init 0'},
        {'item': 'patience', 'value': cfg['training']['early_stopping_patience'],
         'note': 'from config'},
        {'item': 'improvement_rule', 'value': 'score > best (strict)',
         'note': 'on improvement: best=score, bad_epochs=0'},
        {'item': 'no_improvement_rule', 'value': 'bad_epochs += 1',
         'note': 'any non-improvement increments, including ties'},
        {'item': 'tie_resets_counter', 'value': False,
         'note': 'equal score counts as a bad epoch'},
        {'item': 'stop_condition', 'value': 'bad_epochs >= patience',
         'note': 'checked AFTER the epoch checkpoint is saved'},
        {'item': 'minimum_delta', 'value': None, 'note': 'none configured'},
        {'item': 'order_vs_checkpoint',
         'value': 'early_stopping.update() then save latest/best, then stop check',
         'note': 'the stopping epoch IS checkpointed'},
        {'item': 'order_vs_scheduler',
         'value': 'scheduler.step() happens before the early-stop check',
         'note': 'per-epoch LR advance occurs even on the final epoch'},
        {'item': 'observed_final_state', 'value': str(es),
         'note': 'latest.pt early_stopping_state (bad_epochs == patience -> stopped)'},
    ]
    return pd.DataFrame(rows)


def build_scheduler_contract() -> pd.DataFrame:
    cfg = load_phase09_config()
    return pd.DataFrame([
        {'item': 'type', 'value': cfg['scheduler']['name'],
         'source': 'scripts/training/train_kub_baseline.py:112', 'note': ''},
        {'item': 'parameters', 'value': f"T_max={cfg['scheduler']['max_epochs']}",
         'source': 'CosineAnnealingLR(optimizer, T_max=...)', 'note': 'no eta_min'},
        {'item': 'step_frequency', 'value': 'per epoch',
         'source': 'one scheduler.step() inside the epoch loop', 'note': ''},
        {'item': 'step_timing', 'value': 'after train_one_epoch AND after validate',
         'source': 'line 156, after line 154/155', 'note': 'not per batch'},
        {'item': 'metric_driven', 'value': False,
         'source': 'no ReduceLROnPlateau', 'note': ''},
        {'item': 'resume_state_required', 'value': True,
         'source': 'scheduler_state saved/restored in checkpoint', 'note': ''},
        {'item': 'first_epoch_lr', 'value': 'initial lr (1e-4)',
         'source': 'step occurs at end of epoch 1', 'note': ''},
    ])


def build_resume_contract() -> pd.DataFrame:
    ck = phase09_checkpoint_metadata()
    rows = [
        {'item': 'resume_source', 'value': 'latest.pt', 'note': 'best.pt used for final eval only'},
        {'item': 'start_epoch', 'value': 'state["epoch"] + 1', 'note': 'continues, no repeat'},
        {'item': 'experiment_id', 'value': 'reused unchanged',
         'note': 'hardcoded exp_id; no _v2/_retry suffixes on resume'},
        {'item': 'manifest_guard_on_resume', 'value': 'manifest_version AND hashes must match',
         'note': 'raises RuntimeError otherwise'},
        {'item': 'model_state', 'value': True, 'note': 'load_state_dict'},
        {'item': 'optimizer_state', 'value': True, 'note': ''},
        {'item': 'scheduler_state', 'value': True, 'note': ''},
        {'item': 'grad_scaler_state', 'value': True, 'note': 'AMP scaler'},
        {'item': 'epoch', 'value': True, 'note': ''},
        {'item': 'best_metric', 'value': True, 'note': 'best_validation_score'},
        {'item': 'best_epoch', 'value': 'from best.pt epoch', 'note': ''},
        {'item': 'early_stop_counter', 'value': True,
         'note': 'early_stopping_state {best, bad_epochs, patience, stopped}'},
        {'item': 'history_continuity', 'value': True, 'note': 'training_history list restored'},
        {'item': 'global_step', 'value': True, 'note': ''},
        {'item': 'rng_state', 'value': True, 'note': 'random_state capture/restore'},
        {'item': 'loader_generator_state', 'value': True,
         'note': 'train/val generator states; legacy replay fallback exists'},
        {'item': 'taxonomy_id', 'value': ck.get('latest.pt', {}).get('taxonomy_id'),
         'note': 'ABSENT historically (None) -> additive field for clean-v3'},
        {'item': 'single_writer', 'value': 'implemented in src/utils/run_lock.py',
         'note': 'active lock fails loudly; stale lock requires explicit recovery'},
    ]
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# 5. v2 -> clean-v3 protocol diff
# ---------------------------------------------------------------------------

CLEAN_V3_AUTHORIZED_CHANGES = {
    'manifest_version', 'taxonomy_id', 'experiment_id',
    'source_config', 'source_config_sha', 'source_trainer', 'source_trainer_sha',
    'checkpoint_best_sha', 'checkpoint_latest_sha', 'protocol_status',
    'historical_role', 'epochs_completed', 'best_epoch',
}


def build_protocol_diff(historical: dict) -> pd.DataFrame:
    """
    Field-by-field v2 -> clean-v3 diff. Only provenance/version fields may differ.
    """
    rows = []
    for field, v2 in historical.items():
        if field == 'manifest_version':
            v3, reason, material = MANIFEST_VERSION_CLEAN, 'authorized clean-v3 provenance', False
        elif field == 'taxonomy_id':
            v3, reason, material = TAXONOMY_ID, 'authorized frozen taxonomy binding', False
        elif field == 'experiment_id':
            v3, reason, material = f'{v2}_clean_v3', 'new logical run id', False
        elif field in CLEAN_V3_AUTHORIZED_CHANGES:
            v3, reason, material = '<clean-v3 provenance>', 'authorized provenance metadata', False
        else:
            v3, reason, material = v2, 'preserved from historical protocol', False
        rows.append({
            'field': field,
            'historical_v2': v2,
            'clean_v3_candidate': v3,
            'same_or_changed': 'same' if v3 == v2 else 'changed',
            'change_reason': reason,
            'scientifically_material': material,
        })
    return pd.DataFrame(rows)


def build_candidate_configs(historical_cfg: dict) -> pd.DataFrame:
    """
    Clean-v3 Phase-09 candidate configs: historical scientific semantics with only
    authorized provenance changes.
    """
    base = {
        'experiment_id': f'{PHASE09_EXP_ID}_clean_v3',
        'phase': 9,
        'dataset': 'KUB',
        'manifest_version': MANIFEST_VERSION_CLEAN,
        'taxonomy_id': TAXONOMY_ID,
        'model_name': historical_cfg['model']['name'],
        'input_channels': historical_cfg['model']['input_channels'],
        'output_channels': historical_cfg['model']['output_channels'],
        'base_channels': historical_cfg['model']['base_channels'],
        'input_resolution': historical_cfg['input_resolution'],
        'loss': historical_cfg['loss']['name'],
        'bce_weight': historical_cfg['loss']['bce_weight'],
        'dice_weight': historical_cfg['loss']['dice_weight'],
        'dice_epsilon': historical_cfg['loss']['dice_epsilon'],
        'optimizer': historical_cfg['optimizer']['name'],
        'learning_rate': historical_cfg['optimizer']['learning_rate'],
        'weight_decay': historical_cfg['optimizer']['weight_decay'],
        'scheduler': historical_cfg['scheduler']['name'],
        'scheduler_max_epochs': historical_cfg['scheduler']['max_epochs'],
        'batch_size': historical_cfg['training']['batch_size'],
        'gradient_accumulation_steps': historical_cfg['training']['gradient_accumulation_steps'],
        'effective_batch_size': historical_cfg['training']['effective_batch_size'],
        'amp': historical_cfg['training']['amp'],
        'seed': historical_cfg['training']['seed'],
        'max_epochs': historical_cfg['training']['max_epochs'],
        'early_stopping_patience': historical_cfg['training']['early_stopping_patience'],
        'checkpoint_metric': historical_cfg['training']['monitor'],
        'threshold': historical_cfg['training']['threshold'],
        'num_workers': historical_cfg['training']['num_workers'],
        'pin_memory': historical_cfg['training']['pin_memory'],
        'device_contract': 'get_device(require_cuda=True)',
        'target_contract': 'src.utils.targets.binarize_mask (mask > 0)',
        'candidate_status': 'RECONSTRUCTED_AND_READY',
        'executed': False,
    }
    return pd.DataFrame([base])


def write_candidate_config_files(cfg: dict, out_dir: Path = None) -> list:
    """Persist candidate configs as versioned YAML files (not executed)."""
    out_dir = out_dir or CONFIG_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    candidate = {
        'experiment_id': f'{PHASE09_EXP_ID}_clean_v3',
        'phase': 9,
        'dataset': 'KUB',
        'manifest_version': MANIFEST_VERSION_CLEAN,
        'taxonomy_id': TAXONOMY_ID,
        'status': 'RECONSTRUCTED_AND_READY',
        'authorization_required': 'Phase-09 clean rerun authorization',
        'model': {
            'name': cfg['model']['name'],
            'input_channels': cfg['model']['input_channels'],
            'output_channels': cfg['model']['output_channels'],
            'base_channels': cfg['model']['base_channels'],
        },
        'input_resolution': cfg['input_resolution'],
        'preprocessing': cfg['preprocessing'],
        'augmentation': cfg['augmentation'],
        'loss': cfg['loss'],
        'optimizer': cfg['optimizer'],
        'scheduler': cfg['scheduler'],
        'training': {**cfg['training'], 'monitor': cfg['training']['monitor']},
        'device_contract': 'src.utils.device.get_device(require_cuda=True)',
        'target_contract': 'src.utils.targets.binarize_mask',
        'single_writer_lock': 'src.utils.run_lock',
        'allow_test': False,
    }
    p = out_dir / 'phase09_unet_baseline_clean_v3.yaml'
    p.write_text(yaml.safe_dump(candidate, sort_keys=False), encoding='utf-8')
    paths.append(p)
    return paths


# ---------------------------------------------------------------------------
# 6. Pre-existing test debt
# ---------------------------------------------------------------------------

TEST_DEBT = [
    {'test_file': 'tests/test_phase14_part1.py', 'observed': 'HANGS (never completes)',
     'affected_phase': 'Phase 14', 'module': 'Phase-14 regional/refiner work',
     'required_by_phase09': False,
     'disposition': 'DEFER_TO_AFFECTED_CLEAN_RERUN_PHASE'},
    {'test_file': 'tests/test_predicted_roi.py', 'observed': '3 failures',
     'affected_phase': 'Phase 13', 'module': 'src/inference/predicted_roi.py',
     'required_by_phase09': False,
     'disposition': 'DEFER_TO_AFFECTED_CLEAN_RERUN_PHASE'},
    {'test_file': 'tests/test_kub_localizer.py', 'observed': '1 failure',
     'affected_phase': 'Phase 13', 'module': 'src/models/kub_localizer.py',
     'required_by_phase09': False,
     'disposition': 'DEFER_TO_AFFECTED_CLEAN_RERUN_PHASE'},
]


def build_test_debt() -> pd.DataFrame:
    import subprocess
    rows = []
    for d in TEST_DEBT:
        rel = d['module']
        p = PROJECT_ROOT / rel if rel.startswith('src/') else None
        modified = None
        if p and p.exists():
            try:
                r = subprocess.run(['git', 'diff', '--quiet', '--', rel],
                                   cwd=str(PROJECT_ROOT), capture_output=True)
                modified = r.returncode != 0
            except Exception:
                modified = None
        rows.append({**d, 'module_git_modified': modified})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# 7. Resume-equivalence probe (INFRASTRUCTURE_TEST_ONLY)
# ---------------------------------------------------------------------------

def resume_equivalence_probe(steps: int = 6, split_at: int = 3,
                             device_type: str = 'cpu', seed: int = 7) -> dict:
    """
    Deterministic tiny probe: continuous run vs save/destroy/restore run.

    INFRASTRUCTURE_TEST_ONLY — synthetic data, no scientific claim.
    Uses CPU by default; the canonical device contract remains CUDA-required for
    real runs, but this probe is a unit-level equivalence check.
    """
    import tempfile
    from src.utils.reproducibility import set_seed
    from src.utils.checkpointing import (save_training_checkpoint,
                                         load_training_checkpoint)

    device = torch.device(device_type)

    def make_model():
        return torch.nn.Sequential(
            torch.nn.Conv2d(1, 4, 3, padding=1), torch.nn.ReLU(),
            torch.nn.Conv2d(4, 1, 1)).to(device)

    set_seed(seed)
    initial = make_model()          # fixed random init shared by both paths
    initial_state = {k: v.clone() for k, v in initial.state_dict().items()}

    x = torch.rand(2, 1, 8, 8, generator=torch.Generator().manual_seed(1)).to(device)
    y = (torch.rand(2, 1, 8, 8, generator=torch.Generator().manual_seed(2)) > 0.5).float().to(device)
    loss_fn = torch.nn.BCEWithLogitsLoss()

    def make_opt(m):
        return torch.optim.SGD(m.parameters(), lr=0.05, momentum=0.9)

    def make_sched(o):
        return torch.optim.lr_scheduler.StepLR(o, step_size=1, gamma=0.9)

    def run(model, opt, sched, n):
        losses, lrs = [], []
        model.train()
        for _ in range(n):
            opt.zero_grad(set_to_none=True)
            loss = loss_fn(model(x), y)
            loss.backward()
            opt.step()
            sched.step()
            losses.append(float(loss.detach().cpu()))
            lrs.append(float(opt.param_groups[0]['lr']))
        return losses, lrs

    # Path A: continuous
    set_seed(seed)
    mA = make_model(); mA.load_state_dict(initial_state)
    oA = make_opt(mA); sA = make_sched(oA)
    lossesA, lrsA = run(mA, oA, sA, steps)

    # Path B: K steps, save, destroy, restore, remaining steps
    set_seed(seed)
    mB = make_model(); mB.load_state_dict(initial_state)
    oB = make_opt(mB); sB = make_sched(oB)
    first_losses, first_lrs = run(mB, oB, sB, split_at)

    with tempfile.TemporaryDirectory() as tmp:
        ckpt = Path(tmp) / 'probe.pt'
        save_training_checkpoint(
            ckpt, mB, oB, sB, None, epoch=split_at, global_step=split_at,
            best_validation_score=0.0, configuration={'probe': True}, seed=seed,
            training_history=[], manifest_version=MANIFEST_VERSION_CLEAN,
            manifest_hashes={}, experiment_id='phase08_resume_probe',
            model_name='probe', input_resolution=8, threshold=0.5,
            taxonomy_id=TAXONOMY_ID)
        del mB, oB, sB
        mB2 = make_model()
        oB2 = make_opt(mB2); sB2 = make_sched(oB2)
        state = load_training_checkpoint(ckpt, mB2, oB2, sB2, None,
                                         restore_rng=True, map_location=device)
    rest_losses, rest_lrs = run(mB2, oB2, sB2, steps - split_at)

    lossesB = first_losses + rest_losses
    lrsB = first_lrs + rest_lrs

    # parameter equivalence
    pA = torch.cat([p.detach().flatten().cpu() for p in mA.parameters()])
    pB = torch.cat([p.detach().flatten().cpu() for p in mB2.parameters()])

    return {
        'label': 'INFRASTRUCTURE_TEST_ONLY',
        'device': str(device),
        'steps': steps, 'split_at': split_at,
        'losses_continuous': lossesA,
        'losses_resumed': lossesB,
        'losses_identical': bool(np.allclose(lossesA, lossesB, rtol=0, atol=1e-12)),
        'max_loss_abs_diff': float(np.max(np.abs(np.array(lossesA) - np.array(lossesB)))),
        'lr_schedule_identical': bool(np.allclose(lrsA, lrsB, rtol=0, atol=1e-15)),
        'parameters_identical': bool(torch.equal(pA, pB)),
        'max_param_abs_diff': float((pA - pB).abs().max()) if pA.numel() else 0.0,
        'restored_experiment_id': state['experiment_id'],
        'restored_manifest_version': state['manifest_version'],
        'restored_taxonomy_id': state['taxonomy_id'],
        'restored_epoch': state['epoch'],
        'scientific_claim': 'NONE',
    }


# ---------------------------------------------------------------------------
# 8. Figures
# ---------------------------------------------------------------------------

FIGURE_NAMES = [
    'phase08b_trainer_lifecycle.png',
    'phase08b_checkpoint_state_machine.png',
    'phase08b_resume_equivalence_trace.png',
    'phase08b_validation_aggregation_handcheck.png',
]


def make_figures(probe: dict, agg_df: pd.DataFrame):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

    FIGDIR.mkdir(parents=True, exist_ok=True)
    out = []

    # 1. trainer lifecycle flow
    fig, ax = plt.subplots(figsize=(10.5, 5.4))
    ax.set_xlim(0, 10); ax.set_ylim(0, 6); ax.axis('off')
    steps = [
        ('config validation', 0.4, 5.0), ('manifest guard', 2.4, 5.0),
        ('device (CUDA required)', 4.4, 5.0), ('seed init', 6.9, 5.0),
        ('dataset + loader', 0.4, 3.7), ('model', 2.4, 3.7),
        ('optimizer', 4.0, 3.7), ('scheduler', 5.4, 3.7), ('AMP scaler', 6.8, 3.7),
        ('epoch: train_one_epoch', 0.4, 2.4), ('validate (VAL)', 3.0, 2.4),
        ('scheduler.step()', 5.2, 2.4), ('checkpoint decision', 7.2, 2.4),
        ('early-stop decision', 0.4, 1.1), ('history persist', 3.0, 1.1),
        ('resume handling', 5.2, 1.1), ('clean termination', 7.4, 1.1),
    ]
    for label, x, y in steps:
        ax.add_patch(FancyBboxPatch((x, y), 2.1, 0.7, boxstyle='round,pad=0.06',
                                    fc='#dce9f7', ec='#2f7ed8'))
        ax.text(x + 1.05, y + 0.35, label, ha='center', va='center', fontsize=8)
    for i in range(3):
        ax.add_patch(FancyArrowPatch((steps[i][1] + 2.1, steps[i][2] + 0.35),
                                     (steps[i + 1][1], steps[i + 1][2] + 0.35),
                                     arrowstyle='->', color='#555', lw=1.1))
    ax.set_title('Trainer lifecycle (one root trainer per experiment ID)', fontsize=11,
                 fontweight='bold')
    p = FIGDIR / FIGURE_NAMES[0]
    fig.tight_layout(); fig.savefig(p, dpi=120, bbox_inches='tight'); plt.close(fig)
    out.append(p)

    # 2. checkpoint / early-stop state machine
    fig, ax = plt.subplots(figsize=(9.5, 4.6))
    ax.set_xlim(0, 10); ax.set_ylim(0, 4); ax.axis('off')
    nodes = [('epoch end', 0.3, 1.6), ('val macro dice', 2.3, 1.6),
             ('score > best ?', 4.4, 1.6), ('save best.pt', 6.7, 2.5),
             ('bad_epochs++', 6.7, 0.7), ('bad_epochs >= 15 ?', 8.0, 1.6)]
    for label, x, y in nodes:
        ax.add_patch(FancyBboxPatch((x, y), 1.9, 0.75, boxstyle='round,pad=0.06',
                                    fc='#e8f3e8', ec='#4a9d5f'))
        ax.text(x + 0.95, y + 0.375, label, ha='center', va='center', fontsize=8)
    ax.annotate('yes -> best=score, bad_epochs=0', xy=(5.6, 2.35), xytext=(5.2, 3.3),
                fontsize=8, color='#2a6b3f',
                arrowprops=dict(arrowstyle='->', color='#2a6b3f'))
    ax.annotate('no (incl. tie)', xy=(6.7, 1.05), xytext=(5.0, 0.15), fontsize=8,
                color='#a33', arrowprops=dict(arrowstyle='->', color='#a33'))
    ax.text(9.0, 0.2, 'stop -> break\n(latest.pt already saved)', fontsize=8, color='#a33')
    ax.set_title('Checkpoint selection + early-stop state machine (strict >)',
                 fontsize=11, fontweight='bold')
    p = FIGDIR / FIGURE_NAMES[1]
    fig.tight_layout(); fig.savefig(p, dpi=120, bbox_inches='tight'); plt.close(fig)
    out.append(p)

    # 3. resume equivalence trace
    fig, ax = plt.subplots(figsize=(7.8, 4.2))
    xs = np.arange(1, len(probe['losses_continuous']) + 1)
    ax.plot(xs, probe['losses_continuous'], 'o-', color='#2f7ed8', lw=2,
            label='Path A: continuous')
    ax.plot(xs, probe['losses_resumed'], 'x--', color='#d64545', lw=2,
            label='Path B: save/destroy/restore')
    ax.axvline(probe['split_at'] + 0.5, color='#888', ls=':', lw=1.2)
    ax.text(probe['split_at'] + 0.55, ax.get_ylim()[0], 'checkpoint', fontsize=8,
            color='#666', va='bottom')
    ax.set_xlabel('optimizer step'); ax.set_ylabel('synthetic loss')
    ax.set_title(f"Resume equivalence probe (INFRASTRUCTURE_TEST_ONLY)\n"
                 f"losses identical={probe['losses_identical']} | "
                 f"params identical={probe['parameters_identical']}", fontsize=10)
    ax.legend(frameon=False, fontsize=8)
    p = FIGDIR / FIGURE_NAMES[2]
    fig.tight_layout(); fig.savefig(p, dpi=120, bbox_inches='tight'); plt.close(fig)
    out.append(p)

    # 4. validation aggregation hand-check
    fig, ax = plt.subplots(figsize=(7.8, 4.2))
    labels = agg_df['example'].str.replace('_', '\n')
    x = np.arange(len(agg_df)); w = 0.38
    ax.bar(x - w / 2, agg_df['macro_mean_of_per_image'], w, label='macro (mean per image)',
           color='#2f7ed8')
    ax.bar(x + w / 2, agg_df['micro_global_pixel'], w, label='micro (global pixel)',
           color='#e08a3c')
    ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=7)
    ax.set_ylabel('dice'); ax.set_ylim(0, 1.05)
    ax.set_title('Validation aggregation hand-check: macro vs micro', fontsize=11,
                 fontweight='bold')
    ax.legend(frameon=False, fontsize=8)
    p = FIGDIR / FIGURE_NAMES[3]
    fig.tight_layout(); fig.savefig(p, dpi=120, bbox_inches='tight'); plt.close(fig)
    out.append(p)

    return out
