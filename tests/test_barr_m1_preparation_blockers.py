"""Targeted synthetic checks; never invoke a scientific execution command."""
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import mock_open, patch

import numpy as np
import pandas as pd

SOURCE = Path(__file__).resolve().parents[1] / "scripts/analysis/barr_m1_reanalysis_execute_v1_0d.py"
spec = importlib.util.spec_from_file_location("barr_candidate", SOURCE)
h = importlib.util.module_from_spec(spec)
spec.loader.exec_module(h)


class PreparationChecks(unittest.TestCase):
    def test_missing_authorization_refused(self):
        with self.assertRaises(h.AuthorizationError):
            h.load_and_verify_authorization(None)

    def test_unsigned_self_asserted_authorization_refused(self):
        # Entirely synthetic record sent to the retired entrypoint's production
        # guard. No approval artifact, data loader, or execution entrypoint runs.
        record = dict(study_identifier="BARR-M1", authorized_by="SYNTHETIC",
                      authorization_id="NOT-AN-APPROVAL", approval_date="invalid-date",
                      arms=["A0", "A1", "A8"], population="ROUTER_DEVELOPMENT n=4957",
                      execution_mode="CPU_ONLY_RE_ANALYSIS_ONLY",
                      protocol_sha256="a" * 64, harness_sha256="a" * 64)
        with self.assertRaises(h.AuthorizationError):
            h.load_and_verify_authorization(record)

    def test_wrong_k_refused(self):
        n = h.N_EXPECTED
        domains = ["BUSI"] * 512 + ["ISIC"] * 2173 + ["KUB"] * 1680 + ["KVASIR"] * 592
        ids = ["synthetic_%s" % i for i in range(n)]
        frames = {
            "phase25c_oof_labels": pd.DataFrame(dict(sample_id=ids, delta_dice=np.zeros(n))),
            "phase25e_c8_membership": pd.DataFrame(dict(sample_id=ids, selected=np.zeros(n))),
            "phase25f_oof_safety": pd.DataFrame(dict(sample_id=ids, p_accept_oof=np.ones(n))),
            "phase25b_dev_metadata": pd.DataFrame(dict(sample_id=ids, domain=domains)),
        }
        with self.assertRaises(h.ExecutionError):
            joined = h.validate_population(frames)
            h.construct_deltas(joined)


if __name__ == "__main__":
    unittest.main()
