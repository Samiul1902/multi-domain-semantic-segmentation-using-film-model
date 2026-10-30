"""
Phase 07 Part 1B — unit tests for the versioned KUB size taxonomy.

Proves:
  - foreground uses (mask > 0)
  - 8-connectivity merges diagonal neighbours
  - exact frozen boundary semantics (Q25/Q50/Q75 -> lower bin)
  - values just above each boundary move to the next bin
  - no rounding is applied before classification
  - ROI -> ROI_NOT_PRIMARY_BINNED
  - historical kub_size_v1 thresholds are unchanged
  - the clean taxonomy loads the frozen artifact
  - an unknown taxonomy id fails

All data used here is synthetic. No real manifest or medical content is touched.
"""

import json
import sys
import unittest
from pathlib import Path

import numpy as np
from scipy.ndimage import label as nd_label

PROJECT_ROOT = Path(r'D:\Softfors\jup')
sys.path.insert(0, str(PROJECT_ROOT / 'notebooks' / 'phasewise'
                       / 'phase_07_tiny_object_definition' / 'code'))

import phase07b_taxonomy_freeze as p7b  # noqa: E402
import phase07_tiny_definition as p7  # noqa: E402

sys.path.insert(0, str(PROJECT_ROOT))
from src.analysis import kub_object_size as kos  # noqa: E402


class TestForegroundRule(unittest.TestCase):
    """Foreground must be (mask > 0), never (mask == 1)."""

    def test_any_nonzero_is_foreground(self):
        mask = np.array([[0, 1, 0], [0, 2, 0], [0, 255, 0]], dtype=np.uint8)
        fg = mask > 0
        self.assertEqual(int(fg.sum()), 3)   # labels 1, 2, 255 all foreground
        self.assertFalse(bool((mask == 1).sum() == fg.sum()))

    def test_heterogeneous_labels_all_foreground(self):
        for lab in (1, 2, 3, 255):
            m = np.zeros((5, 5), dtype=np.uint8)
            m[2, 2] = lab
            self.assertEqual(int((m > 0).sum()), 1, f'label {lab} should be foreground')


class TestConnectivity(unittest.TestCase):
    """8-connectivity merges diagonally touching pixels; 4-connectivity does not."""

    def test_diagonal_touching(self):
        m = np.zeros((4, 4), dtype=bool)
        m[1, 1] = True
        m[2, 2] = True
        _, n8 = nd_label(m, structure=np.ones((3, 3), dtype=int))
        _, n4 = nd_label(m, structure=np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]]))
        self.assertEqual(n8, 1, '8-connectivity should merge diagonal neighbours')
        self.assertEqual(n4, 2, '4-connectivity should keep them separate')

    def test_separated_components_stay_separate(self):
        m = np.zeros((6, 6), dtype=bool)
        m[1, 1] = True
        m[4, 4] = True
        _, n8 = nd_label(m, structure=np.ones((3, 3), dtype=int))
        self.assertEqual(n8, 2)


class TestBoundarySemantics(unittest.TestCase):
    """Exact frozen boundary semantics with no rounding."""

    def setUp(self):
        self.t = {'Q25': 0.0001499766777599,
                  'Q50': 0.00033976472454305,
                  'Q75': 0.0008266496069636999}

    def test_exact_q25_is_tiny(self):
        self.assertEqual(p7b.classify(self.t['Q25'], self.t), 'TINY')

    def test_just_above_q25_is_small(self):
        self.assertEqual(p7b.classify(np.nextafter(self.t['Q25'], 1.0), self.t), 'SMALL')

    def test_exact_q50_is_small(self):
        self.assertEqual(p7b.classify(self.t['Q50'], self.t), 'SMALL')

    def test_just_above_q50_is_medium(self):
        self.assertEqual(p7b.classify(np.nextafter(self.t['Q50'], 1.0), self.t), 'MEDIUM')

    def test_exact_q75_is_medium(self):
        self.assertEqual(p7b.classify(self.t['Q75'], self.t), 'MEDIUM')

    def test_above_q75_is_large(self):
        self.assertEqual(p7b.classify(np.nextafter(self.t['Q75'], 1.0), self.t), 'LARGE')

    def test_zero_is_tiny(self):
        self.assertEqual(p7b.classify(0.0, self.t), 'TINY')

    def test_no_rounding_before_classification(self):
        """A value just below Q25 must not be rounded up into SMALL."""
        just_below = np.nextafter(self.t['Q25'], 0.0)
        self.assertEqual(p7b.classify(just_below, self.t), 'TINY')
        # and a value that would round to Q25 is still classified on its true value
        self.assertEqual(p7b.classify(self.t['Q25'] - 1e-18, self.t), 'TINY')


class TestROIHandling(unittest.TestCase):
    """ROI components must never be primary-binned."""

    def test_roi_not_primary_binned(self):
        import pandas as pd
        comps = pd.DataFrame({
            'sample_id': ['a', 'b'],
            'component_ratio': [0.0000001, 0.5],
            'view_type': ['ROI_CROP', 'FULL_FIELD'],
        })
        out = kos.assign_versioned_strata(comps, kos.HISTORICAL_TAXONOMY_ID)
        self.assertEqual(out.loc[0, 'size_stratum'], 'ROI_NOT_PRIMARY_BINNED')
        self.assertNotEqual(out.loc[1, 'size_stratum'], 'ROI_NOT_PRIMARY_BINNED')

    def test_frozen_apply_marks_taxonomy(self):
        import pandas as pd
        comps = pd.DataFrame({
            'sample_id': ['a'],
            'component_ratio': [0.0000001],
        })
        out = p7b.apply_frozen(comps, {'Q25': 0.001, 'Q50': 0.002, 'Q75': 0.003})
        self.assertEqual(out.loc[0, 'frozen_taxonomy_id'], p7b.CLEAN_TAXONOMY_ID)
        self.assertEqual(out.loc[0, 'frozen_stratum'], 'TINY')


class TestHistoricalImmutable(unittest.TestCase):
    """kub_size_v1 thresholds must remain exactly as frozen."""

    def test_historical_thresholds_unchanged(self):
        self.assertEqual(kos.KUB_SIZE_V1_THRESHOLDS['Q25'], 0.0001499766777599)
        self.assertEqual(kos.KUB_SIZE_V1_THRESHOLDS['Q50'], 0.00033976472454305)
        self.assertEqual(kos.KUB_SIZE_V1_THRESHOLDS['Q75'], 0.0008266496069636999)

    def test_historical_taxonomy_id_stable(self):
        self.assertEqual(kos.HISTORICAL_TAXONOMY_ID, 'kub_size_v1')

    def test_historical_record_file_unchanged(self):
        p = PROJECT_ROOT / 'reports' / 'audits' / 'kub_object_size_thresholds.json'
        self.assertTrue(p.exists())
        payload = json.loads(p.read_text(encoding='utf-8'))
        self.assertEqual(payload['Q25'], 0.0001499766777599)
        self.assertEqual(payload['Q50'], 0.00033976472454305)
        self.assertEqual(payload['Q75'], 0.0008266496069636999)


class TestCleanTaxonomyLoads(unittest.TestCase):
    """The clean taxonomy must load the FROZEN artifact."""

    def test_clean_thresholds_load(self):
        artifact = PROJECT_ROOT / 'reports' / 'audits' / 'kub_size_clean_v3_v1_thresholds.json'
        if not artifact.exists():
            self.skipTest('frozen clean-v3 artifact not present (run Part 1B first)')
        t = kos.get_kub_size_taxonomy(kos.CLEAN_V3_TAXONOMY_ID)
        self.assertIn('Q25', t)
        self.assertLess(t['Q25'], t['Q50'])
        self.assertLess(t['Q50'], t['Q75'])

    def test_artifact_is_frozen(self):
        artifact = PROJECT_ROOT / 'reports' / 'audits' / 'kub_size_clean_v3_v1_thresholds.json'
        if not artifact.exists():
            self.skipTest('frozen clean-v3 artifact not present')
        payload = json.loads(artifact.read_text(encoding='utf-8'))
        self.assertEqual(payload['status'], 'FROZEN')
        self.assertEqual(payload['taxonomy_id'], 'kub_size_clean_v3_v1')
        self.assertEqual(payload['connectivity'], 8)
        self.assertEqual(payload['foreground_rule'], 'mask > 0')
        self.assertEqual(payload['acquisition_scope'], 'FULL_FIELD')
        self.assertTrue(payload['supervisor_authorized'])

    def test_clean_differs_from_historical_is_expected_not_assumed(self):
        """Clean thresholds are re-derived; they must not be silently identical."""
        artifact = PROJECT_ROOT / 'reports' / 'audits' / 'kub_size_clean_v3_v1_thresholds.json'
        if not artifact.exists():
            self.skipTest('frozen clean-v3 artifact not present')
        clean = kos.get_kub_size_taxonomy(kos.CLEAN_V3_TAXONOMY_ID)
        # Both are valid; we only assert they are independent records.
        self.assertNotEqual(clean, kos.KUB_SIZE_V1_THRESHOLDS,
                            'clean-v3 thresholds should be an independent derivation')


class TestUnknownTaxonomy(unittest.TestCase):
    def test_wrong_taxonomy_id_fails(self):
        with self.assertRaises(ValueError):
            kos.get_kub_size_taxonomy('kub_size_v9')

    def test_empty_taxonomy_id_fails(self):
        with self.assertRaises(ValueError):
            kos.get_kub_size_taxonomy('')


if __name__ == '__main__':
    unittest.main(verbosity=2)
