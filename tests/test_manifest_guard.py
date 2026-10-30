"""
Phase 05 Part 1E — Manifest Guard Version-Aware Unit Tests.

Proves that src/utils/manifest_guard.py:
  - validates phase4_v2 (historical) expected hashes successfully
  - validates phase4_v3 (canonical active) expected hashes successfully
  - FAILS on a wrong v3 train hash (via synthetic temp copy)
  - FAILS on a wrong version/hash pairing
  - confirms TEST SHA is identical under v2 and v3
  - recognises the v3 quarantine file

Failure tests operate ONLY on synthetic temporary copies.
No real manifest file is ever modified or written to.
"""

import shutil
import tempfile
import unittest
from pathlib import Path

from src.utils.manifest_guard import (
    _V2_HASHES,
    _V3_HASHES,
    _V3_FILE_MAP,
    verify_manifests,
    validate_manifest_version,
    validate_manifest_version_strict,
    get_canonical_hash,
    get_manifest_path,
    _sha256,
)

PROJECT_ROOT = Path(r'D:\Softfors\jup')
V2_DIR = PROJECT_ROOT / 'manifests'
V3_DIR = PROJECT_ROOT / 'manifests' / 'phase4_v3'


class TestManifestGuardLegacy(unittest.TestCase):
    """Legacy interface must keep working (backward compatibility)."""

    def test_legacy_verify_manifests_passes(self):
        # Should not raise
        verify_manifests()


class TestV2Validation(unittest.TestCase):
    """phase4_v2 (historical) validation must still PASS."""

    def test_v2_full_validation_passes(self):
        result = validate_manifest_version('phase4_v2')
        self.assertTrue(result['ok'], f"v2 validation failed: {result}")
        self.assertEqual(sorted(result['passed']),
                         sorted(['all_paired', 'train', 'val', 'test']))
        self.assertEqual(result['failed'], [])
        self.assertEqual(result['missing'], [])

    def test_v2_strict_does_not_raise(self):
        validate_manifest_version_strict('phase4_v2')


class TestV3Validation(unittest.TestCase):
    """phase4_v3 (canonical active development) validation must PASS."""

    def test_v3_full_validation_passes(self):
        result = validate_manifest_version('phase4_v3')
        self.assertTrue(result['ok'], f"v3 validation failed: {result}")
        self.assertEqual(len(result['passed']), 7)
        self.assertEqual(result['failed'], [])
        self.assertEqual(result['missing'], [])

    def test_v3_strict_does_not_raise(self):
        validate_manifest_version_strict('phase4_v3')

    def test_v3_quarantine_file_recognised(self):
        # quarantine artifact must be part of the v3 registry and validate
        self.assertIn('quarantined', _V3_HASHES)
        result = validate_manifest_version('phase4_v3', subset=['quarantined'])
        self.assertTrue(result['ok'], f"quarantine validation failed: {result}")
        self.assertEqual(result['passed'], ['quarantined'])

    def test_v3_extended_artifacts_recognised(self):
        for key in ('quarantined', 'duplicate_groups', 'grouping_provenance'):
            self.assertIn(key, _V3_HASHES, f"{key} missing from v3 registry")
            self.assertTrue(_V3_FILE_MAP[key].exists(), f"{key} file missing")


class TestTestImmutableAcrossVersions(unittest.TestCase):
    """TEST must be byte-identical under v2 and v3."""

    def test_test_hash_identical(self):
        self.assertEqual(
            get_canonical_hash('phase4_v2', 'test'),
            get_canonical_hash('phase4_v3', 'test'),
        )

    def test_test_actual_hash_matches_both_registries(self):
        actual = _sha256(V2_DIR / 'test.csv')
        self.assertEqual(actual, _V2_HASHES['test'])
        self.assertEqual(actual, _V3_HASHES['test'])
        self.assertEqual(
            actual,
            '9361eba61c91c034a9aa4988a4df229bba591a5cbd553c98689ac7915da29727',
        )

    def test_v3_test_identical_to_v2_test_bytes(self):
        a = _sha256(V2_DIR / 'test.csv')
        b = _sha256(V3_DIR / 'test.csv')
        self.assertEqual(a, b)


class TestFailureModes(unittest.TestCase):
    """Failure tests use synthetic temp copies. Real manifests untouched."""

    def test_wrong_v3_train_hash_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmpdir = Path(tmp)
            # Copy real v3 files into a temp dir, then corrupt train.csv
            for key, src in _V3_FILE_MAP.items():
                shutil.copy2(src, tmpdir / f'{key}.csv')
            with open(tmpdir / 'train.csv', 'ab') as f:
                f.write(b'\n#synthetic-corruption-for-test\n')

            import src.utils.manifest_guard as guard
            original_dir = guard._V3_DIR
            original_map = guard._V3_FILE_MAP
            try:
                guard._V3_DIR = tmpdir
                guard._V3_FILE_MAP = {k: tmpdir / f'{k}.csv' for k in _V3_HASHES}
                guard._VERSION_REGISTRY['phase4_v3'] = {
                    'hashes': guard._V3_HASHES,
                    'file_map': guard._V3_FILE_MAP,
                }
                result = guard.validate_manifest_version('phase4_v3')
                self.assertFalse(result['ok'], "Corrupted train.csv must FAIL")
                failed_keys = [item['key'] for item in result['failed']]
                self.assertIn('train', failed_keys)

                with self.assertRaises(ValueError):
                    guard.validate_manifest_version_strict('phase4_v3')
            finally:
                guard._V3_DIR = original_dir
                guard._V3_FILE_MAP = original_map
                guard._VERSION_REGISTRY['phase4_v3'] = {
                    'hashes': guard._V3_HASHES,
                    'file_map': original_map,
                }

    def test_wrong_version_hash_pairing_fails(self):
        """Pointing a version at the wrong directory yields a mismatch."""
        import src.utils.manifest_guard as guard
        original_map = guard._V3_FILE_MAP
        try:
            # Pair v3 expected hashes with the v2 root directory files
            guard._V3_FILE_MAP = {k: V2_DIR / f'{k}.csv' for k in _V3_HASHES
                                  if (V2_DIR / f'{k}.csv').exists()}
            guard._VERSION_REGISTRY['phase4_v3'] = {
                'hashes': guard._V3_HASHES,
                'file_map': guard._V3_FILE_MAP,
            }
            result = guard.validate_manifest_version(
                'phase4_v3', subset=['train', 'val'])
            # v2 train/val must NOT match v3 train/val expected hashes
            failed_keys = [item['key'] for item in result['failed']]
            self.assertIn('train', failed_keys)
            self.assertIn('val', failed_keys)
            self.assertFalse(result['ok'])
        finally:
            guard._V3_FILE_MAP = original_map
            guard._VERSION_REGISTRY['phase4_v3'] = {
                'hashes': guard._V3_HASHES,
                'file_map': original_map,
            }

    def test_unknown_version_raises(self):
        with self.assertRaises(ValueError):
            validate_manifest_version('phase4_v9')

    def test_real_manifests_unmodified_by_failure_tests(self):
        """Guard against accidental writes to real manifests."""
        result_v2 = validate_manifest_version('phase4_v2')
        result_v3 = validate_manifest_version('phase4_v3')
        self.assertTrue(result_v2['ok'])
        self.assertTrue(result_v3['ok'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
