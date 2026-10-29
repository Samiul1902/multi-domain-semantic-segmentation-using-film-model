"""
Unit and Contract Tests for R3 Prospective Analysis, C1 Schema, Ties and Multiplicity.
"""

import pytest
import numpy as np
import scipy.stats as stats
from src.research.evaluation_r3.analysis_contract import R3AnalysisContract
from src.research.evaluation_r1.metrics import (
    binary_metrics,
    surface_metrics,
    c1_compatibility
)
from src.research.evaluation_r1.statistics import (
    describe,
    paired_summary,
    adjust_pvalues
)


def test_r3_c1_record_validation():
    valid_record = {
        "arm": "C1-T",
        "seed": 42,
        "model_checkpoint_sha256": "abc123",
        "training_config_sha256": "def456",
        "dataset_manifest_sha256": "ghi789",
        "per_domain_results": {"KUB": 0.85, "ISIC": 0.88, "BUSI": 0.80, "KVASIR": 0.82},
        "selected_epoch": 25,
        "duration_seconds": 1200.5,
        "gpu_peak_memory_mb": 4500,
        "metric_version": "c1_phase21_compatibility_v1"
    }
    res = R3AnalysisContract.validate_c1_run_record(valid_record)
    assert res["valid"]

    # Invalid arm
    bad_arm = valid_record.copy()
    bad_arm["arm"] = "C1-UNKNOWN"
    assert not R3AnalysisContract.validate_c1_run_record(bad_arm)["valid"]

    # Invalid seed
    bad_seed = valid_record.copy()
    bad_seed["seed"] = 999
    assert not R3AnalysisContract.validate_c1_run_record(bad_seed)["valid"]

    # Missing domain
    bad_dom = valid_record.copy()
    bad_dom["per_domain_results"] = {"KUB": 0.85, "ISIC": 0.88}
    assert not R3AnalysisContract.validate_c1_run_record(bad_dom)["valid"]


def test_r3_equal_domain_macro_calculation():
    domain_scores = {"KUB": 0.80, "ISIC": 0.90, "BUSI": 0.70, "KVASIR": 0.80}
    macro = R3AnalysisContract.compute_equal_domain_macro(domain_scores)
    assert np.isclose(macro, 0.80)


def test_r3_c1_summary_table_structure():
    t_records = {
        42: {"per_domain_results": {"KUB": 0.85, "ISIC": 0.88, "BUSI": 0.80, "KVASIR": 0.82}},
        123: {"per_domain_results": {"KUB": 0.84, "ISIC": 0.87, "BUSI": 0.81, "KVASIR": 0.83}},
        3407: {"per_domain_results": {"KUB": 0.86, "ISIC": 0.89, "BUSI": 0.79, "KVASIR": 0.84}}
    }
    c_records = {
        42: {"per_domain_results": {"KUB": 0.82, "ISIC": 0.85, "BUSI": 0.78, "KVASIR": 0.80}},
        123: {"per_domain_results": {"KUB": 0.81, "ISIC": 0.84, "BUSI": 0.79, "KVASIR": 0.81}},
        3407: {"per_domain_results": {"KUB": 0.83, "ISIC": 0.86, "BUSI": 0.77, "KVASIR": 0.82}}
    }

    table = R3AnalysisContract.format_c1_summary_table(t_records, c_records, (0.015, 0.035))
    assert table["status"] == "SYNTHETIC_TEST_ONLY"
    assert len(table["per_seed_rows"]) == 3
    # 42 delta: 0.8375 - 0.8125 = 0.025
    # 123 delta: 0.8375 - 0.8125 = 0.025
    # 3407 delta: 0.845 - 0.820 = 0.025
    # mean = 0.025
    assert np.isclose(table["mean_paired_delta"], 0.025)
    assert table["seed_sample_sd"] >= 0


def test_r3_wilcoxon_ties_and_zeros_handling():
    d_with_zeros = np.array([0.0, 0.0, 0.02, -0.01, 0.03, 0.02, 0.04, 0.0, -0.01, 0.05])
    res_pratt = stats.wilcoxon(d_with_zeros, zero_method="pratt")
    res_wilc = stats.wilcoxon(d_with_zeros, zero_method="wilcox")
    assert res_pratt.pvalue is not None
    assert res_wilc.pvalue is not None
