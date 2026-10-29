"""
Unit and Contract Tests for R2 Evaluation Engine, Split Integrity & Statistical Validation
"""

import pytest
import numpy as np
import scipy.stats as stats
from src.research.evaluation_r2.leakage_contract import LeakageAuditContract
from src.research.evaluation_r1.metrics import (
    binary_metrics,
    multiclass_metrics,
    surface_metrics,
    c1_compatibility
)
from src.research.evaluation_r1.statistics import (
    describe,
    paired_summary,
    adjust_pvalues
)


def test_leakage_contract_prohibited_splits():
    contract = LeakageAuditContract()
    dummy_prob = np.zeros((32, 32), dtype=np.float32)
    dummy_gt = np.zeros((32, 32), dtype=np.uint8)

    for bad_split in ["TEST", "test", "ROUTER_HOLDOUT", "QUARANTINE", "EXTERNAL"]:
        res = contract.validate_evaluation_request(
            split=bad_split,
            domain="KUB",
            probabilities=dummy_prob,
            ground_truth=dummy_gt
        )
        assert not res["valid"]
        assert "PROHIBITED_SPLIT_ACCESS" in res["reason"]


def test_leakage_contract_aliases_and_warnings():
    contract = LeakageAuditContract()
    dummy_prob = np.full((32, 32), 0.5, dtype=np.float32)
    dummy_gt = np.ones((32, 32), dtype=np.uint8)

    # Test DERM alias canonicalization & patient ID warning
    res = contract.validate_evaluation_request(
        split="VAL",
        domain="DERM",
        probabilities=dummy_prob,
        ground_truth=dummy_gt,
        spacing=(0.5, 0.5),
        patient_id="patient_ISIC_001"
    )
    assert res["valid"]
    assert res["canonical_domain"] == "ISIC"
    assert res["spacing_unit"] == "pixel"
    assert not res["cluster_bootstrap_eligible"]
    assert any("PHYSICAL_SPACING_UNVERIFIED" in w for w in res["warnings"])
    assert any("UNVERIFIED_PATIENT_ID" in w for w in res["warnings"])

    # Test KUB with patient ID
    res_kub = contract.validate_evaluation_request(
        split="VAL",
        domain="KUB-StoneX",
        probabilities=dummy_prob,
        ground_truth=dummy_gt,
        patient_id="patient-00001"
    )
    assert res_kub["valid"]
    assert res_kub["canonical_domain"] == "KUB"
    assert res_kub["cluster_bootstrap_eligible"]


def test_leakage_split_disjointness_checker():
    contract = LeakageAuditContract()

    train_samples = {"s1", "s2", "s3"}
    val_samples = {"s4", "s5", "s6"}
    train_patients = {"s1": "p1", "s2": "p2", "s3": "p3"}
    val_patients = {"s4": "p4", "s5": "p5", "s6": "p6"}

    # Perfect disjointness
    res = contract.verify_split_disjointness(train_samples, val_samples, train_patients, val_patients)
    assert res["status"] == "PASS"
    assert res["sample_disjoint"]
    assert res["patient_disjoint"]

    # Leaked sample
    val_samples_leaked = {"s3", "s4", "s5"}
    res_leak = contract.verify_split_disjointness(train_samples, val_samples_leaked)
    assert res_leak["status"] == "FAIL_LEAKAGE"
    assert not res_leak["sample_disjoint"]

    # Leaked patient
    val_patients_leaked = {"s4": "p1", "s5": "p5", "s6": "p6"}
    res_p_leak = contract.verify_split_disjointness(train_samples, val_samples, train_patients, val_patients_leaked)
    assert res_p_leak["status"] == "FAIL_PATIENT_LEAKAGE"
    assert not res_p_leak["patient_disjoint"]


def test_independent_mathematical_metrics():
    # 1. Pixel counts and overlap
    # pred: row0=[1,1], row1=[0,0] -> 2 ones
    # gt:   row0=[1,0], row1=[1,0] -> 2 ones
    # overlap: (0,0) is 1 in both -> TP=1
    # FP: (0,1) is pred=1, gt=0 -> FP=1
    # FN: (1,0) is pred=0, gt=1 -> FN=1
    # TN: (1,1) is pred=0, gt=0 -> TN=1
    # 2*TP / (2*TP + FP + FN) = 2*1 / (2 + 1 + 1) = 2/4 = 0.5
    pred = np.array([[1, 1], [0, 0]], dtype=np.uint8)
    gt = np.array([[1, 0], [1, 0]], dtype=np.uint8)
    m = binary_metrics(pred, gt)
    assert m["tp"] == 1
    assert m["fp"] == 1
    assert m["fn"] == 1
    assert m["tn"] == 1
    assert np.isclose(m["dice"], 0.5)
    assert np.isclose(m["iou"], 1.0 / 3.0)
    assert np.isclose(m["precision"], 0.5)
    assert np.isclose(m["recall"], 0.5)
    assert np.isclose(m["specificity"], 0.5)

    # 2. Both empty convention
    empty = np.zeros((10, 10), dtype=np.uint8)
    m_ee = binary_metrics(empty, empty)
    assert m_ee["dice"] == 1.0
    assert m_ee["iou"] == 1.0

    # 3. One empty convention
    nonempty = np.zeros((10, 10), dtype=np.uint8)
    nonempty[2:5, 2:5] = 1
    m_oe = binary_metrics(nonempty, empty)
    assert m_oe["dice"] == 0.0
    assert m_oe["iou"] == 0.0


def test_independent_statistical_tests():
    rng = np.random.default_rng(12345)
    treatment = rng.normal(0.85, 0.05, size=20)
    control = rng.normal(0.80, 0.05, size=20)

    # Check sample standard deviation ddof=1 via describe
    diffs = treatment - control
    stats_desc = describe(diffs)
    sample_sd = stats_desc["sample_sd"]
    # Compare against scipy
    assert np.isclose(sample_sd, stats.tstd(diffs))
    assert np.isclose(stats_desc["mean"], np.mean(diffs))

    # Check paired_summary statistics
    p_sum = paired_summary(treatment, control)
    assert np.isclose(p_sum["mean"], np.mean(diffs))
    assert np.isclose(p_sum["sample_sd"], sample_sd)
    assert p_sum["n_expected_pairs"] == 20
    assert p_sum["n_missing_pairs"] == 0
    assert p_sum["n_improved"] == int(np.count_nonzero(diffs > 0))

    # Check multiplicity adjustments
    raw_p = [0.001, 0.01, 0.04, 0.05, 0.20]
    p_holm = adjust_pvalues(raw_p, method="holm")
    p_bh = adjust_pvalues(raw_p, method="bh")
    assert all(h >= r for h, r in zip(p_holm, raw_p))
    assert all(b >= r for b, r in zip(p_bh, raw_p))
