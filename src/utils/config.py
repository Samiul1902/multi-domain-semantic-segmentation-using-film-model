"""
Experiment configuration foundation (Phase 08 Part 1A).

Two responsibilities:

1. Load YAML/JSON configuration files (historical behaviour, preserved).
2. Define the canonical experiment configuration schema and validate it.

Governance: this module may declare which fields are REQUIRED, but it must NOT
silently choose scientifically material defaults for architecture, loss,
learning rate, weight decay, scheduler, augmentation, threshold, checkpoint
metric, or early stopping. Those must be stated explicitly in an experiment
config.
"""
from __future__ import annotations

import json
from pathlib import Path

import yaml

# ---------------------------------------------------------------------------
# Canonical experiment configuration schema
# ---------------------------------------------------------------------------

#: Fields that MUST be present in a canonical experiment config. No default is
#: supplied for any of them: a missing value is an error, not an implicit choice.
REQUIRED_SCIENTIFIC_FIELDS = (
    'experiment_id',
    'manifest_version',
    'dataset',
    'architecture',
    'input_resolution',
    'loss',
    'optimizer',
    'learning_rate',
    'weight_decay',
    'scheduler',
    'batch_size',
    'amp',
    'seed',
    'augmentation_policy',
    'checkpoint_metric',
    'early_stopping',
    'taxonomy_id',
)

#: Non-scientific provenance fields recorded alongside the scientific ones.
PROVENANCE_FIELDS = (
    'phase',
    'notes',
    'git_commit',
)

CANONICAL_CONFIG_FIELDS = REQUIRED_SCIENTIFIC_FIELDS + PROVENANCE_FIELDS

#: Values that must never be assumed when the field is absent.
FORBIDDEN_IMPLICIT_DEFAULTS = (
    'architecture', 'loss', 'learning_rate', 'weight_decay', 'scheduler',
    'augmentation_policy', 'threshold', 'checkpoint_metric', 'early_stopping',
)

#: Sentinel values that mark a field as not-yet-specified. Any occurrence makes
#: the config invalid: these must never be treated as a scientific choice.
PLACEHOLDER_VALUES = ('<REQUIRED>', 'REQUIRED', 'TODO', 'TBD', 'PLACEHOLDER',
                      'DEFAULT', 'default', '', None)

CANONICAL_MANIFEST_VERSION = 'phase4_v3'


class ConfigValidationError(ValueError):
    """Raised when an experiment config is incomplete or inconsistent."""


def load_config(config_path):
    """Load a YAML or JSON configuration file (historical interface)."""
    config_path = str(config_path)
    with open(config_path, 'r', encoding='utf-8') as f:
        if config_path.endswith('.yaml') or config_path.endswith('.yml'):
            return yaml.safe_load(f)
        elif config_path.endswith('.json'):
            return json.load(f)
    return None


def validate_experiment_config(config: dict, require_all: bool = True) -> dict:
    """
    Validate an experiment configuration against the canonical schema.

    Parameters
    ----------
    config : dict
        The configuration to validate.
    require_all : bool
        When True (canonical), every REQUIRED_SCIENTIFIC_FIELDS entry must be
        present. When False, only structural checks are performed (useful for
        partially-specified infrastructure placeholders).

    Returns
    -------
    dict
        ``{'valid': bool, 'missing': [...], 'present': [...], 'errors': [...]}``

    Notes
    -----
    This function NEVER fills in a scientific value. A missing field is reported,
    not defaulted.
    """
    if not isinstance(config, dict):
        raise ConfigValidationError('config must be a mapping')

    present = [k for k in CANONICAL_CONFIG_FIELDS if k in config]
    missing = [k for k in REQUIRED_SCIENTIFIC_FIELDS if k not in config]

    errors = []
    if require_all and missing:
        errors.append(f'missing required scientific fields: {missing}')

    if 'manifest_version' in config and config['manifest_version'] != CANONICAL_MANIFEST_VERSION:
        errors.append(
            f"manifest_version is {config['manifest_version']!r}; canonical "
            f"development requires {CANONICAL_MANIFEST_VERSION!r}")

    # A placeholder is not a scientific choice: reject it anywhere it appears.
    placeholders = sorted(k for k, v in config.items() if v in PLACEHOLDER_VALUES)
    if placeholders:
        errors.append(
            f'fields still holding placeholder/unspecified values: {placeholders}')

    for key in FORBIDDEN_IMPLICIT_DEFAULTS:
        if key in config and config[key] in PLACEHOLDER_VALUES:
            errors.append(f"field {key!r} must not be a placeholder/default value")

    return {
        'valid': not errors and (not require_all or not missing),
        'present': present,
        'missing': missing,
        'placeholder_fields': placeholders,
        'errors': errors,
    }


def write_experiment_config(config: dict, path) -> Path:
    """Persist an experiment config as JSON (machine-readable)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config, indent=2, default=str), encoding='utf-8')
    return path


def config_template(placeholders: bool = True) -> dict:
    """
    Return a schema template.

    With ``placeholders=True`` every required field is present but set to the
    explicit string ``'<REQUIRED>'`` so it cannot be mistaken for a scientific
    choice. Callers must replace each one before use.
    """
    value = '<REQUIRED>' if placeholders else None
    template = {k: value for k in REQUIRED_SCIENTIFIC_FIELDS}
    template['manifest_version'] = CANONICAL_MANIFEST_VERSION
    template['taxonomy_id'] = 'kub_size_clean_v3_v1'
    return template
