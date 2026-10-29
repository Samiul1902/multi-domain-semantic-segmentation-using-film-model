"""Synthetic artifact, aggregation and statistical validation."""
import copy
import hashlib
import json
import numpy as np
import pytest
from src.research.evaluation_r1.artifacts import validate_artifacts, array_sha256
from src.research.evaluation_r1.aggregation import evaluate, grouped_summary, equal_domain_macro, failure_breakdown
from src.research.evaluation_r1.statistics import describe, paired_summary, paired_bootstrap, adjust_pvalues, budget_quality
from src.research.evaluation_r1.synthetic import fixture, report_bytes


def reseal(r):
    m = r["metadata"]
    m["probability_sha256"] = array_sha256(r["probability"])
    m["ground_truth_sha256"] = array_sha256(r["ground_truth"])
    m.pop("metadata_sha256", None)
    m["metadata_sha256"] = hashlib.sha256(json.dumps(m, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def test_artifacts_validation_and_rejection():
    base = fixture(); assert validate_artifacts(base)["sample_count"] == 4
    for mutation in ("split", "shape", "schema", "ids", "probability", "missing", "checkpoint", "duplicate", "hash"):
        r = copy.deepcopy(base)
        if mutation == "split": r[0]["metadata"]["split"] = "TEST"
        if mutation == "shape": r[0]["probability"] = np.zeros((2,2))
        if mutation == "schema": r[0]["metadata"]["class_schema_version"] = "wrong"
        if mutation == "ids": r[0]["ground_truth"][0,0] = 2
        if mutation == "probability": r[0]["probability"][0,0] = np.nan
        if mutation == "missing": del r[0]["metadata"]["model_id"]
        if mutation == "checkpoint": r[0]["metadata"]["checkpoint_sha256"] = "1"*64
        if mutation == "duplicate": r[1]["metadata"]["sample_id"] = r[0]["metadata"]["sample_id"]
        if mutation == "hash": r[0]["probability"][0,0] = .2
        if mutation not in ("missing", "probability", "hash"): reseal(r[0] if mutation != "duplicate" else r[1])
        with pytest.raises(ValueError): validate_artifacts(r)
    r = copy.deepcopy(base); r[0]["metadata"]["split"] = "ROUTER_HOLDOUT"
    with pytest.raises(ValueError): validate_artifacts(r)


def test_aggregation_and_reproducibility():
    images = evaluate(fixture()); macro = equal_domain_macro(images)
    assert macro["value"] == pytest.approx((1 + 2/3 + 1 + 0)/4)
    assert macro["worst_domain"] == "KUB" and images[0]["annotated_subclass"] == "NOT_AVAILABLE"
    assert sum(failure_breakdown(images).values()) == 4
    assert len(grouped_summary(images, "domain")) == 4
    assert report_bytes() == report_bytes()


def test_statistics_and_missingness():
    assert describe([1, 2, np.nan])["n_missing"] == 1
    assert paired_summary([1, np.nan, 3], [0, 1, 1])["mean"] == 1.5
    assert paired_summary([1, np.nan], [0, 1])["n_missing_pairs"] == 1
    assert adjust_pvalues([.01, .04, .03], "holm") == pytest.approx([.03,.06,.06])
    assert adjust_pvalues([.01, .04, .03], "bh") == pytest.approx([.03,.04,.04])
    assert adjust_pvalues([.01, .04], "bonferroni") == pytest.approx([.02,.08])
    assert budget_quality([{"model":"x","budget":2,"budget_unit":"ms","quality":.5,"quality_metric":"dice"}])[0]["budget"] == 2
    with pytest.raises(ValueError): paired_summary([1,2], [1])


def test_cluster_bootstrap_shared_draws_and_equal_domains():
    rows = []
    for d, vals in (("KUB", [0, 0, 1]), ("ISIC", [1])):
        for i, x in enumerate(vals):
            for s in (1, 2):
                rows.append({"domain":d,"sample_id":f"{d}-{i}","seed":s,"treatment":x,"control":0,
                             "patient_id":("p1" if i < 2 else "p2") if d == "KUB" else None})
    kw = dict(seeds=(1,2), domains=("KUB","ISIC"), n_boot=100, rng_seed=5)
    a = paired_bootstrap(rows, **kw); b = paired_bootstrap(rows, **kw)
    assert a == b and a["estimate"] == pytest.approx((1/3+1)/2)
    assert a["cluster_counts"] == {"KUB":2,"ISIC":1}
    with pytest.raises(ValueError): paired_bootstrap(rows[:-1], **kw)
    bad = copy.deepcopy(rows); bad[0]["patient_id"] = None
    with pytest.raises(ValueError): paired_bootstrap(bad, **kw)
