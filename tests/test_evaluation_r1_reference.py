"""Independent geometry/resampling calculations, explicit tolerance 1e-12."""
import copy
from dataclasses import FrozenInstanceError
import numpy as np
import pytest
from scipy.spatial.distance import cdist
from src.research.evaluation_r1.metrics import surface_metrics
from src.research.evaluation_r1.statistics import paired_bootstrap, c1_primary, match_models, run_accounting, subgroup_effects, equal_budget_comparison
from src.research.evaluation_r1.artifacts import freeze_artifacts, validate_artifacts
from src.research.evaluation_r1.ontology import load_ontology, domain_schema
from src.research.evaluation_r1.aggregation import evaluate, grouped_summary, class_summary, equal_domain_macro
from src.research.evaluation_r1.synthetic import fixture


def test_surface_reference_enumeration():
    # Independent boundary enumeration + brute-force Euclidean distances; no EDT.
    g = np.zeros((7,8), bool); g[0:3,0:3] = True; g[5,6] = True
    p = np.zeros_like(g); p[1:4,1:4] = True; p[5,7] = True
    def points(mask):
        result = []
        for r, c in np.argwhere(mask):
            if any(not (0 <= r+dr < mask.shape[0] and 0 <= c+dc < mask.shape[1]) or not mask[r+dr,c+dc]
                   for dr in (-1,0,1) for dc in (-1,0,1)):
                result.append((r*2.5,c*.75))
        return np.array(result)
    distances = cdist(points(p), points(g))
    a, b = distances.min(axis=1), distances.min(axis=0)
    all_dist = np.r_[a,b]
    got = surface_metrics(p,g,spacing=(2.5,.75),tolerance=1)
    assert got["hausdorff"] == pytest.approx(max(a.max(),b.max()), abs=1e-12, rel=0)
    assert got["hd95"] == pytest.approx(np.percentile(all_dist,95), abs=1e-12, rel=0)
    assert got["assd"] == pytest.approx(sum(all_dist)/len(all_dist), abs=1e-12, rel=0)
    assert got["surface_dice"] == pytest.approx((sum(a<=1)+sum(b<=1))/(len(a)+len(b)), abs=1e-12, rel=0)


def test_shared_seed_bootstrap_cancellation_and_cluster_weight():
    # Seed effects cancel per case, so every shared-draw resample is exactly zero.
    rows = [{"domain":"KUB","sample_id":str(i),"seed":s,"treatment": x if s==1 else -x,
             "control":0,"patient_id":"a" if i<2 else "b"}
            for i,x in enumerate((0,2,10)) for s in (1,2)]
    got = paired_bootstrap(rows,seeds=(1,2),domains=("KUB",),n_boot=50,rng_seed=7)
    assert got["ci"] == [0,0] and got["bootstrap_distribution_sd"] == 0
    assert got["per_seed"]["1"] == 4 and got["per_seed"]["2"] == -4
    one = [r for r in rows if r["seed"]==1]
    got = paired_bootstrap(one,seeds=(1,),domains=("KUB",),n_boot=50,rng_seed=7)
    rng = np.random.Generator(np.random.PCG64(7)); expected=[]
    clusters = [[0,2],[10]]
    for _ in range(50):
        selected = rng.integers(0,2,size=2)
        values = [v for idx in selected for v in clusters[idx]]
        expected.append(sum(values)/len(values))
    assert got["ci"] == pytest.approx(np.quantile(expected,[.025,.975]),abs=1e-12,rel=0)
    assert got["bootstrap_distribution_sd"] == pytest.approx(np.std(expected,ddof=1),abs=1e-12,rel=0)


def test_immutable_contract_and_ontology():
    records = fixture(); frozen = freeze_artifacts(records)
    records[0]["probability"][0,0] = .8
    assert frozen[0].record()["probability"][0,0] == 0
    with pytest.raises(ValueError): frozen[0].record()["probability"][0,0] = 1
    with pytest.raises(FrozenInstanceError): frozen[0].shape = (1,)
    assert load_ontology()["schema_version"] == "harmonized_binary_v1"
    assert domain_schema("KUB")["classes"][1] == "stone"
    with pytest.raises(ValueError): domain_schema("invented")
    r = fixture(); r[0]["metadata"]["source_path"] = "some/TEST/pred.npy"
    with pytest.raises(ValueError): validate_artifacts(r)


def test_grouping_missing_ids_and_equal_domain_not_pooled():
    images = evaluate(fixture())
    patients = grouped_summary(images,"patient_id")
    missing = [r for r in patients if r["status"]=="NOT_AVAILABLE"]
    assert len(missing)==3 and all(r["mean"] is None and r["n_missing_group_ids"]==1 for r in missing)
    assert len(class_summary(images))==16
    duplicated = images + [copy.deepcopy(images[0]) for _ in range(4)]
    assert equal_domain_macro(images)["value"] == equal_domain_macro(duplicated)["value"]
    assert np.mean([r["foreground"]["dice"] for r in duplicated]) != equal_domain_macro(duplicated)["value"]
    with pytest.raises(ValueError): equal_domain_macro(images[:-1])


def test_run_join_subgroup_budget_accounting():
    a = [{"domain":"KUB","sample_id":"a","seed":1,"patient_id":"p","value":.7}]
    b = [{**a[0],"value":.5}]
    assert match_models(a,b)["rows"][0]["treatment"]==.7
    assert len(match_models(a,[])["unmatched_treatment"])==1
    with pytest.raises(ValueError): match_models(a+a,b)
    assert not run_accounting([],arms=("T","C"),seeds=(1,))["primary_ready"]
    assert subgroup_effects([{"treatment":1,"control":0}])[0]["status"]=="NOT_AVAILABLE"
    cost=[{"sample_id":"a","budget":2,"budget_unit":"ms","quality":.7}]
    assert equal_budget_comparison(cost,[{**cost[0],"quality":.5}],budget_unit="ms")["quality"]["mean"]==pytest.approx(.2)
    with pytest.raises(ValueError): equal_budget_comparison(cost,[{**cost[0],"budget":3}],budget_unit="ms")


def test_c1_frozen_plan_and_run_failure():
    domains=("ISIC","BUSI","KVASIR","KUB"); seeds=(42,123,3407)
    roster=[{"domain":d,"sample_id":f"s-{d}","patient_id":"synthetic-p" if d=="KUB" else None} for d in domains]
    rows=[{**r,"seed":s,"treatment":.75,"control":.5,"split":"SYNTHETIC",
           "metric_version":"c1_phase21_compatibility_v1","threshold":.5} for r in roster for s in seeds]
    runs=[{"arm":a,"seed":s,"status":"COMPLETE"} for a in ("C1-T","C1-C") for s in seeds]
    got=c1_primary(rows,runs=runs,expected_samples=roster)
    assert got["estimate"]==.25 and got["ci"]==[.25,.25]
    assert got["resamples"]==10000 and got["rng_seed"]==20261027 and not got["claim_authorized"]
    with pytest.raises(ValueError): c1_primary(rows,runs=runs[:-1],expected_samples=roster)
    with pytest.raises(ValueError): c1_primary(rows[:-1],runs=runs,expected_samples=roster)
    bad=copy.deepcopy(runs); bad[0]["status"]="FAILED"
    with pytest.raises(ValueError): c1_primary(rows,runs=bad,expected_samples=roster)


def test_writer_reproducible_and_refuses_overwrite(tmp_path):
    from src.research.evaluation_r1.synthetic import write_examples
    first=write_examples(tmp_path)
    assert first==write_examples(tmp_path)
    content=(tmp_path/"synthetic_results.json").read_text()
    assert "SYNTHETIC_TEST_ONLY" in content
    (tmp_path/"synthetic_example_table.csv").write_text("unrelated")
    with pytest.raises(ValueError): write_examples(tmp_path)


def test_spacing_area_and_invalid_probability_artifacts():
    import hashlib, json
    from src.research.evaluation_r1.artifacts import array_sha256
    def seal(r):
        m=r["metadata"]; m.pop("metadata_sha256",None)
        m["probability_sha256"]=array_sha256(r["probability"])
        m["metadata_sha256"]=hashlib.sha256(json.dumps(m,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()
    r=fixture(); r[0]["metadata"]["spacing"]=[2,.5]; seal(r[0])
    assert evaluate(r)[0]["area"]=={"unit":"mm2","reference":1,"predicted":1,"signed_error":0}
    for bad in (np.inf,-.1,1.1):
        r=fixture(); r[0]["probability"][0,0]=bad
        if np.isfinite(bad): seal(r[0])
        with pytest.raises(ValueError): validate_artifacts(r)
    r=fixture(); r[0]["extra"]="not allowed"
    with pytest.raises(ValueError): freeze_artifacts(r)


def test_pooled_pixels_and_surface_missing_counts():
    from src.research.evaluation_r1.aggregation import pooled_pixel_summary, surface_summary
    images=evaluate(fixture())
    pooled=pooled_pixel_summary(images)
    assert (pooled["tp"],pooled["fp"],pooled["tn"],pooled["fn"])==(3,1,31,1)
    assert pooled["dice"]==.75 and pooled["iou"]==.6
    surfaces=surface_summary(images)
    assert len(surfaces)==24
    assert all(r["n_missing"]==1 and r["mean"] is None for r in surfaces if r["group"]=="KUB")
    assert surfaces[0]["unit"]=="pixel"


def test_code_identity_drift_and_unavailable_subgroup():
    from src.research.evaluation_r1 import code_identity
    assert len(code_identity())==64
    r=fixture(); r[0]["metadata"]["evaluation_code_sha256"]="1"*64
    with pytest.raises(ValueError): validate_artifacts(r)
    result=subgroup_effects([{"treatment":1,"control":0}])[0]
    assert result["summary"]["mean"] is None
