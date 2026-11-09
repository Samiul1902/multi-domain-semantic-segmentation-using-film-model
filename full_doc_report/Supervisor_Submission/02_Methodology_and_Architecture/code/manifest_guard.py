import json
import hashlib
from pathlib import Path

PROJECT_ROOT = Path(r'D:\Softfors\jup')

# ---------------------------------------------------------------------------
# Canonical frozen hashes per manifest version
# ---------------------------------------------------------------------------

# phase4_v2: original canonical splits (historical, superseded for new work).
# Required to reproduce historical Phases 06-15.
# Leakage status: KNOWN_SPLIT_CONTAMINATION_DISCOVERED_RETROSPECTIVELY
_V2_HASHES = {
    'all_paired': '66350d465209e4bf0948a16f0da213abb9f8f87c0b222ead7632d2350463f7cc',
    'train':      'd67b549a6cc80b579dfaf4976b9b51630f6d703d8c6bfb33188355cfa6056bc3',
    'val':        '46079b594ed9535c2de953bb976684b8b0bab30c27c6e6e4f2b9f9314b4cc5f4',
    'test':       '9361eba61c91c034a9aa4988a4df229bba591a5cbd553c98689ac7915da29727',
}
_V2_DIR = PROJECT_ROOT / 'manifests'
_V2_FILE_MAP = {
    'all_paired': _V2_DIR / 'all_paired.csv',
    'train':      _V2_DIR / 'train.csv',
    'val':        _V2_DIR / 'val.csv',
    'test':       _V2_DIR / 'test.csv',
}

# phase4_v3: leakage-safe canonical splits (CANONICAL_ACTIVE_DEVELOPMENT).
# All future clean scientific work must use this version.
# 118 development samples quarantined. TEST byte-identical to v2.
_V3_HASHES = {
    'all_paired':         'eb3062fa0e84f9952f994df79ed4d767417a912e18dce86560f6e2edcdd02ded',
    'train':              '28702fc3a5ff8b950db372f03232d335e3a30b1fc2f21db7cd8c066055826ed6',
    'val':                '082c80b2bda63fd73f371f109c34643adf01edaead921643fb2e44993ba53315',
    'test':               '9361eba61c91c034a9aa4988a4df229bba591a5cbd553c98689ac7915da29727',
    'quarantined':        'a4ec1a8c46692f3c2d55d03c73569ce7b44aeeef734abd41e31bf5bf3e60059c',
    'duplicate_groups':   '830d3c0ce08f735081e5a44fe3a740031da1c70cfc19ebcb4ef89c31acd704fb',
    'grouping_provenance':'3eff84851d33e1c8b5894ce05049433287067a5e6088a90f5c67394230317f66',
}
_V3_DIR = PROJECT_ROOT / 'manifests' / 'phase4_v3'
_V3_FILE_MAP = {k: _V3_DIR / f'{k}.csv' for k in _V3_HASHES}

_VERSION_REGISTRY = {
    'phase4_v2': {'hashes': _V2_HASHES, 'file_map': _V2_FILE_MAP},
    'phase4_v3': {'hashes': _V3_HASHES, 'file_map': _V3_FILE_MAP},
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# Original function — PRESERVED for backward compatibility
# Uses manifest_metadata.json (legacy interface, validates v2 root files)
# ---------------------------------------------------------------------------

def verify_manifests():
    """Legacy interface. Validates manifests against manifest_metadata.json."""
    md_path = Path(r'D:\Softfors\jup\manifests\manifest_metadata.json')
    if not md_path.exists():
        raise FileNotFoundError("Metadata not found.")
    with open(md_path, 'r') as f:
        metadata = json.load(f)
    frozen_hashes = metadata.get('hashes', {})
    manifest_dir = md_path.parent
    for file, frozen_hash in frozen_hashes.items():
        p = manifest_dir / f"{file}.csv"
        if not p.exists():
            raise FileNotFoundError(f"{file}.csv missing.")
        hasher = hashlib.sha256()
        with open(p, 'rb') as f:
            while chunk := f.read(8192):
                hasher.update(chunk)
        if hasher.hexdigest() != frozen_hash:
            raise ValueError(f"Manifest hash mismatch for {file}.csv!")
    print("Manifests verified successfully.")


# ---------------------------------------------------------------------------
# New version-explicit interface
# ---------------------------------------------------------------------------

def validate_manifest_version(version: str, subset: list = None) -> dict:
    """
    Validate canonical manifest files for a specific version.

    Parameters
    ----------
    version : str
        'phase4_v2' or 'phase4_v3'
    subset : list, optional
        If given, validate only the listed file keys (e.g. ['train', 'val', 'test']).
        Otherwise validate all files in the version registry.

    Returns
    -------
    dict
        {'version': str, 'passed': list, 'failed': list, 'missing': list, 'ok': bool}

    Raises
    ------
    ValueError
        If version is unknown.

    Notes
    -----
    - Does NOT raise on mismatch by default; returns structured result.
    - Use validate_manifest_version_strict() for raise-on-fail behavior.
    - Historical code that loads phase4_v2 files should call this with
      version='phase4_v2' to verify it is operating on correct frozen data.
    - New code must pass version='phase4_v3'.
    """
    if version not in _VERSION_REGISTRY:
        raise ValueError(
            f"Unknown manifest version '{version}'. "
            f"Valid: {list(_VERSION_REGISTRY.keys())}"
        )
    reg = _VERSION_REGISTRY[version]
    hashes = reg['hashes']
    file_map = reg['file_map']

    keys = subset if subset is not None else list(hashes.keys())
    passed, failed, missing = [], [], []

    for key in keys:
        if key not in hashes:
            raise ValueError(f"Key '{key}' not in version '{version}' registry.")
        path = file_map[key]
        if not path.exists():
            missing.append(key)
            continue
        actual = _sha256(path)
        if actual == hashes[key]:
            passed.append(key)
        else:
            failed.append({'key': key, 'expected': hashes[key], 'actual': actual})

    return {
        'version': version,
        'passed': passed,
        'failed': failed,
        'missing': missing,
        'ok': len(failed) == 0 and len(missing) == 0
    }


def validate_manifest_version_strict(version: str, subset: list = None) -> None:
    """
    Like validate_manifest_version() but raises ValueError on any mismatch.
    Suitable for assertion-style usage in training scripts.
    """
    result = validate_manifest_version(version, subset)
    if not result['ok']:
        problems = []
        for item in result['failed']:
            problems.append(
                f"HASH MISMATCH [{version}] {item['key']}: "
                f"expected {item['expected']}, got {item['actual']}"
            )
        for key in result['missing']:
            problems.append(f"MISSING [{version}] {key}")
        raise ValueError('\n'.join(problems))
    print(f"[manifest_guard] {version} validation PASS ({len(result['passed'])} files)")


def get_canonical_hash(version: str, key: str) -> str:
    """Return the canonical SHA-256 for a given version and file key."""
    if version not in _VERSION_REGISTRY:
        raise ValueError(f"Unknown version '{version}'.")
    hashes = _VERSION_REGISTRY[version]['hashes']
    if key not in hashes:
        raise ValueError(f"Key '{key}' not in version '{version}'.")
    return hashes[key]


def get_manifest_path(version: str, key: str) -> Path:
    """Return the Path for a given version and file key."""
    if version not in _VERSION_REGISTRY:
        raise ValueError(f"Unknown version '{version}'.")
    return _VERSION_REGISTRY[version]['file_map'][key]


if __name__ == '__main__':
    validate_manifest_version_strict('phase4_v2')
    validate_manifest_version_strict('phase4_v3')

